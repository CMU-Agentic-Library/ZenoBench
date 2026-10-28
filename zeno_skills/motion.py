"""cuRobo (GPU) IK, collision checking and joint-space planning against the
scene's real PhysX colliders.

One ``Motion`` per simulator session (runtime.make_rig).  The robot is
robot_sources/curobo/zeno_malo.yml (tools/build_curobo_robot.py): spheres that
Isaac Sim's own generator fitted to each link's PhysX colliders, a virtual
planar base, both arms.  The world is every enabled collider of the stage
(scene_geometry.py), kept at the simulator's poses by ``sync``.

Per arm there are two solvers sharing the robot model: a MotionGen against the
world (collision-aware IK, constraint checks, joint-space trajectories) and an
IKSolver without the world (self-collision only) for kinematic-only moves
(``kin.scene = None``).  Joints a query must not move -- the base pose, the
other arm, the head and the finger leaders -- are locked joints whose fixed
transforms are rewritten in place before each query.

Collision semantics:
  * loose objects are obstacles; the held objects (and what they carry) are
    not, nor is an object whose box (+3 cm) contains a query's TCP target (the
    object being grasped or pushed);
  * ``ignore_fingers`` turns the finger spheres off; ``hand_touches_part`` the
    finger, gripper and wrist-camera spheres (hand on a handle);
  * obstacles farther than CULL m from the base are switched off (speed);
  * base_link has no spheres (its PhysX collider is disabled too).

There is no other solver: a query cuRobo cannot answer fails.
"""

from __future__ import annotations

import atexit
import math
import os
import sys
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

from . import scene_geometry as G
from .kinematics import CARRY_TILT, manipulability, max_tilt, tilt

ROOT = Path(__file__).resolve().parents[1]
ROBOT_CFG = ROOT / "robot_sources/curobo/zeno_malo.yml"
BASE_JOINTS = ("base_x", "base_y", "base_yaw")
CULL = 2.5                 # obstacles beyond this (xy, from the base) are off
RECULL = 0.4               # re-cull when the query base moved this far
TARGET_PAD = 0.03          # an object whose box + this contains the TCP target is not an obstacle
POS_TOL, ROT_TOL = 0.004, 0.04
ACTIVATION = 0.005         # collision margin (m)
FINGER_LINKS = ("gripper_left_finger_link", "gripper_right_finger_link")
HAND_LINKS = FINGER_LINKS + ("gripper_link", "gripper_camera_link")

N_SEEDS = 4               # every IK query passes exactly this many seeds (a new shape re-captures cuRobo's CUDA graphs)
N_RETURN = 8              # and gets this many solutions back
LIMIT_CLEAR = 0.15        # IK prefers arm joints at least this far from their limits
IK_MANIP_W = 0.3          # global IK: weight of (1 - manipulability / best of the batch) in the choice
CLEAR_CAP = 0.05          # m: clearance measured up to this (find_park scores more as equal)
PATH_BATCH = 32           # Cartesian waypoints solved per batched IK call (fixed: CUDA graph shape)
PIN = 1e-3                # half band of a pinned joint (lo == hi)
MAX_STEP = 0.25           # largest joint change between two waypoints of a Cartesian path
TRAJOPT_SEEDS = 12        # trajectory-optimisation seeds per plan (fixed: CUDA graph shape)
GRAPH_SEEDS = 4           # graph-search seeds that seed the optimiser around obstacles
PLAN_ATTEMPTS, PLAN_TIMEOUT = 5, 8.0
APPROACH_FRACTION = 0.5   # constrained Cartesian legs: the last half of the trajectory is the straight approach
APPROACH_ALIGN = 0.95     # |cos| between the leg and a goal-frame axis for a straight-approach constraint
os.environ.setdefault("CUROBO_TORCH_CUDA_GRAPH_RESET", "1")

DIAG = os.environ.get("ZENO_MOTION_DIAG") == "1"     # print why a collision IK was blocked
STATS = {"ik": 0, "ik_ok": 0, "cart": 0, "cart_ok": 0, "plan": 0, "plan_ok": 0, "check": 0,
         "ik_s": 0.0, "cart_s": 0.0, "plan_s": 0.0, "check_s": 0.0, "sync_s": 0.0, "init_s": 0.0}


def _timed(key):
    """Accumulate a Motion method's wall time in STATS[key]."""
    import functools
    import time

    def deco(fn):
        @functools.wraps(fn)
        def wrap(*a, **kw):
            t = time.perf_counter()
            try:
                return fn(*a, **kw)
            finally:
                STATS[key] = round(STATS[key] + time.perf_counter() - t, 3)
        return wrap
    return deco


@atexit.register
def _report():
    if STATS["ik"] or STATS["check"]:
        print(f"[motion] cuRobo queries {STATS}", flush=True)


def _quat_wxyz(R):
    x, y, z, w = Rotation.from_matrix(R).as_quat()
    return [float(w), float(x), float(y), float(z)]


class _Locks:
    """In-place rewrite of locked joints' fixed transforms (cuRobo's own
    update_locked_joints re-parses the URDF: seconds per call)."""

    def __init__(self, models, lock, urdf):
        joints = {j.get("name"): j for j in ET.parse(urdf).getroot().findall("joint")}
        self.models = []
        for m in models:
            kc = m.kinematics_config
            if all(kc.fixed_transforms.data_ptr() != x.fixed_transforms.data_ptr() for x in self.models):
                self.models.append(kc)
        self.entries = {}
        for name, v0 in lock.items():
            j = joints[name]
            child = j.find("child").get("link")
            axis = np.array([float(x) for x in j.find("axis").get("xyz").split()]) if j.find("axis") is not None \
                else np.zeros(3)
            typ = j.get("type")
            per = []
            for kc in self.models:
                i = kc.link_name_to_idx_map[child]
                F0 = kc.fixed_transforms[i].cpu().numpy().astype(float)
                per.append((kc, i, F0 @ np.linalg.inv(self._motion(typ, axis, v0))))
            self.entries[name] = (typ, axis, per)
        self.values = dict(lock)

    @staticmethod
    def _motion(typ, axis, v):
        M = np.eye(4)
        if typ == "prismatic":
            M[:3, 3] = axis * v
        elif typ in ("revolute", "continuous"):
            M[:3, :3] = Rotation.from_rotvec(axis * v).as_matrix()
        return M

    def set(self, values):
        import torch
        for name, v in values.items():
            v = float(v)
            if abs(self.values.get(name, 1e9) - v) < 1e-7:
                continue
            typ, axis, per = self.entries[name]
            M = self._motion(typ, axis, v)
            for kc, i, O in per:
                kc.fixed_transforms[i].copy_(torch.as_tensor(O @ M, device=kc.fixed_transforms.device,
                                                             dtype=kc.fixed_transforms.dtype))
            self.values[name] = v


class _Arm:
    """MotionGen (world) + IKSolver (no world) for one arm, torso lift and waist."""

    def __init__(self, motion, side, cfg, checker):
        import copy

        import torch
        from curobo.types.base import TensorDeviceType
        from curobo.wrap.reacher.ik_solver import IKSolver, IKSolverConfig
        from curobo.wrap.reacher.motion_gen import MotionGen, MotionGenConfig
        from .kinematics import FINGER_OPEN, LEFT_ARM_FOLD, ArmKin

        self.torch, self.side = torch, side
        other = "left" if side == "right" else "right"
        self.kin = ArmKin(side=side)
        self.other_names = ArmKin(side=other).names[2:]
        fold = dict(zip(ArmKin(side="right").names, ArmKin(side="right").posture))
        fold.update(LEFT_ARM_FOLD)
        cfg = copy.deepcopy(cfg)
        k = cfg["kinematics"]
        k["ee_link"] = f"{side}_tcp"
        k["link_names"] = [f"{side}_tcp"]
        lock = {"head_yaw_joint": 0.0, "head_pitch_joint": 0.0,
                "right_gripper_left_finger_axis": FINGER_OPEN, "left_gripper_left_finger_axis": FINGER_OPEN}
        lock.update({n: float(fold.get(n, 0.0)) for n in self.other_names})
        lock.update({n: 0.0 for n in BASE_JOINTS})
        k["lock_joints"] = lock
        ta = TensorDeviceType()
        self.mg = MotionGen(MotionGenConfig.load_from_robot_config(
            cfg, None, ta, world_coll_checker=checker, use_cuda_graph=True, num_ik_seeds=32,
            num_trajopt_seeds=TRAJOPT_SEEDS, num_graph_seeds=GRAPH_SEEDS, interpolation_dt=0.02,
            collision_activation_distance=ACTIVATION, position_threshold=POS_TOL, rotation_threshold=ROT_TOL,
            self_collision_check=True, self_collision_opt=True))
        self.ik_free = IKSolver(IKSolverConfig.load_from_robot_config(
            cfg, None, ta, num_seeds=32, use_cuda_graph=True, self_collision_check=True, self_collision_opt=True,
            position_threshold=POS_TOL, rotation_threshold=ROT_TOL))
        self.ik_path = IKSolver(IKSolverConfig.load_from_robot_config(
            cfg, None, ta, num_seeds=8, use_cuda_graph=True, self_collision_check=True, self_collision_opt=True,
            position_threshold=POS_TOL, rotation_threshold=ROT_TOL))
        assert list(self.mg.joint_names) == list(self.kin.names), (self.mg.joint_names, self.kin.names)
        models = list(self.mg.get_all_kinematics_instances()) + \
            [r.dynamics_model.robot_model for r in self.ik_free.get_all_rollout_instances()] + \
            [r.dynamics_model.robot_model for r in self.ik_path.get_all_rollout_instances()]
        self.locks = _Locks(models, lock, k["urdf_path"])
        # bound costs keep their own copy of the joint limits (BoundCost.set_bounds clones them)
        self.bounds = [r.bound_cost.joint_limits for r in
                       list(self.mg.get_all_rollout_instances()) + list(self.ik_free.get_all_rollout_instances()) +
                       list(self.ik_path.get_all_rollout_instances())
                       if getattr(r, "bound_cost", None) is not None and r.bound_cost.joint_limits is not None]
        self.kcs = self.locks.models
        self.limits = None
        self.lo, self.hi = self.kin.lo.copy(), self.kin.hi.copy()
        self.disabled_links = set()
        self.mg.warmup(enable_graph=True, warmup_js_trajopt=True)
        self.ik_free.solve_single(self._pose(*self.kin.tcp(self.kin.posture)))
        p, R = self.kin.tcp(self.kin.posture)
        self.path_ik([p] * 2, [R] * 2, self.kin.posture)

    # ------------------------------------------------------------- state
    def prepare(self, kin, other_q, links_off):
        """Locks (base pose, other arm), joint limits (kin.lo / kin.hi: skills cap the
        waist or pin the torso) and switched-off links for the next query."""
        yaw = math.atan2(kin.base_R[1, 0], kin.base_R[0, 0])
        vals = {"base_x": kin.base_p[0], "base_y": kin.base_p[1], "base_yaw": yaw}
        if other_q is not None:
            vals.update(zip(self.other_names, np.asarray(other_q, float)[-len(self.other_names):]))
        self.locks.set(vals)
        # a pinned joint (lo == hi: skills hold the torso where it is) gets a +-PIN band: cuRobo's
        # bound cost and projection do not solve with a zero-width range
        lo = np.minimum(kin.lo, kin.hi - 2 * PIN)
        hi = np.maximum(kin.hi, kin.lo + 2 * PIN)
        pinned = (kin.hi - kin.lo) < 2 * PIN
        lo[pinned], hi[pinned] = kin.lo[pinned] - PIN, kin.hi[pinned] + PIN
        self.lo, self.hi = lo, hi
        lim = (tuple(np.round(lo, 6)), tuple(np.round(hi, 6)))
        if lim != self.limits:
            t = self.torch
            for p in [kc.joint_limits.position for kc in self.kcs] + [b.position for b in self.bounds]:
                p[0].copy_(t.as_tensor(lo, device=p.device, dtype=p.dtype))
                p[1].copy_(t.as_tensor(hi, device=p.device, dtype=p.dtype))
            self.limits = lim
        links_off = set(links_off)
        if links_off != self.disabled_links:
            for kc in self.kcs:
                for l in self.disabled_links - links_off:
                    kc.enable_link_spheres(l)
                for l in links_off - self.disabled_links:
                    kc.disable_link_spheres(l)
            self.disabled_links = links_off

    def _pose(self, p, R):
        from curobo.types.math import Pose
        t = self.torch
        return Pose(t.tensor([[*map(float, p)]], device="cuda", dtype=t.float32),
                    t.tensor([_quat_wxyz(R)], device="cuda", dtype=t.float32))

    def _js(self, Q):
        from curobo.types.robot import JointState
        t = self.torch
        Q = t.as_tensor(np.atleast_2d(np.asarray(Q, np.float32)), device="cuda")
        return JointState.from_position(Q, joint_names=list(self.kin.names))

    # ------------------------------------------------------------- queries
    def ik(self, p, R, seeds, collision, local=False):
        """Best solution; ``local``: the successful one closest to seeds[0] (stays on its branch)."""
        t = self.torch
        seeds = [np.clip(np.asarray(s, float), self.lo, self.hi) for s in seeds][:N_SEEDS]
        if local:
            seeds = [seeds[0]] * N_SEEDS
        seeds = (seeds + [self.kin.posture] * N_SEEDS)[:N_SEEDS] if seeds else [self.kin.posture] * N_SEEDS
        seed_t = t.as_tensor(np.array(seeds, np.float32), device="cuda").view(1, N_SEEDS, -1)
        retract = t.as_tensor(np.asarray(seeds[0], np.float32), device="cuda").view(1, -1)
        solver = self.mg if collision else self.ik_free
        r = (solver.solve_ik if collision else solver.solve_single)(
            self._pose(p, R), retract_config=retract, seed_config=seed_t, return_seeds=N_RETURN)
        ok = r.success.view(-1).cpu().numpy().astype(bool)
        Q = r.solution.view(-1, len(self.kin.names)).cpu().numpy().astype(float)
        if not ok.any():
            return Q[0], False
        inside = np.all((Q >= self.lo - 1e-4) & (Q <= self.hi + 1e-4), axis=1)
        ok &= inside
        if not ok.any():
            return Q[0], False
        Q = Q[ok]
        # closest to the first seed, kept clear of the joint limits: a posture on a limit tracks
        # badly under load (a button press at the elbow limit missed by 4 cm)
        near = np.max(np.abs(Q - seeds[0]), axis=1)
        margin = np.min(np.minimum(Q - self.lo, self.hi - Q)[:, 2:], axis=1)
        score = near + 10.0 * np.maximum(0.0, LIMIT_CLEAR - margin)
        if local:                    # never trade continuity for the margin
            score = np.where(near <= MAX_STEP, score, 1e3 + near)
        else:                        # away from singular postures (tracks and pushes better)
            m = np.array([manipulability(self.kin, q) for q in Q])
            score = score + IK_MANIP_W * (1.0 - m / max(float(m.max()), 1e-9))
        return Q[int(np.argmin(score))], True

    def path_ik(self, P, Rs, q0):
        """Kinematic IK for a sequence of TCP poses in batched calls (PATH_BATCH per call, every
        problem seeded with q0 and regularised towards it); chained greedily: each waypoint takes
        the successful solution closest to the previous one.  Returns (qs, ok)."""
        from curobo.types.math import Pose
        t = self.torch
        n_dof = len(self.kin.names)
        out, q = [], np.clip(np.asarray(q0, float), self.lo, self.hi)
        for c in range(0, len(P), PATH_BATCH):
            Pc, Rc = P[c:c + PATH_BATCH], Rs[c:c + PATH_BATCH]
            k = len(Pc)
            pos = np.array(list(Pc) + [Pc[-1]] * (PATH_BATCH - k), np.float32)
            quat = np.array([_quat_wxyz(R) for R in list(Rc) + [Rc[-1]] * (PATH_BATCH - k)], np.float32)
            seed = t.as_tensor(np.tile(q.astype(np.float32), (PATH_BATCH, N_SEEDS, 1)), device="cuda")
            retract = t.as_tensor(np.tile(q.astype(np.float32), (PATH_BATCH, 1)), device="cuda")
            r = self.ik_path.solve_batch(Pose(t.as_tensor(pos, device="cuda"), t.as_tensor(quat, device="cuda")),
                                         retract_config=retract, seed_config=seed, return_seeds=N_RETURN)
            Q = r.solution.view(PATH_BATCH, -1, n_dof).cpu().numpy().astype(float)
            ok = r.success.view(PATH_BATCH, -1).cpu().numpy().astype(bool)
            ok &= np.all((Q >= self.lo - 1e-4) & (Q <= self.hi + 1e-4), axis=2)
            for i in range(k):
                if not ok[i].any():
                    return out, False
                cand = Q[i][ok[i]]
                jump = np.max(np.abs(cand - q), axis=1)
                j = int(np.argmin(jump))
                if jump[j] > MAX_STEP:
                    return out, False
                q = cand[j]
                out.append(q)
        return out, True

    def feasible(self, Q):
        """Per row of Q: inside the limits, no self or world collision."""
        # collision only: a measured posture may sit on a limit the solvers keep clear of
        m = self.mg.check_constraints(self._js(np.clip(np.atleast_2d(Q), self.lo, self.hi)))
        return m.feasible.view(-1).cpu().numpy().astype(bool)

    def plan(self, q0, q1):
        """Joint-space trajectory: graph search seeds the trajectory optimiser around obstacles."""
        from curobo.wrap.reacher.motion_gen import MotionGenPlanConfig
        q0, q1 = np.clip(q0, self.lo, self.hi), np.clip(q1, self.lo, self.hi)
        r = self.mg.plan_single_js(self._js(q0), self._js(q1),
                                   MotionGenPlanConfig(max_attempts=PLAN_ATTEMPTS, enable_graph=True,
                                                       timeout=PLAN_TIMEOUT))
        return self._traj(r)

    def plan_pose(self, q0, p, R, metric=None):
        """Trajectory to a TCP pose under an optional cuRobo PoseCostMetric (constrained planning).
        Graph search joins after two attempts (it ignores the pose constraint, the optimiser
        then enforces it)."""
        from curobo.wrap.reacher.motion_gen import MotionGenPlanConfig
        q0 = np.clip(q0, self.lo, self.hi)
        r = self.mg.plan_single(self._js(q0), self._pose(p, R),
                                MotionGenPlanConfig(max_attempts=PLAN_ATTEMPTS, enable_graph=False,
                                                    enable_graph_attempt=2, timeout=PLAN_TIMEOUT,
                                                    pose_cost_metric=metric))
        return self._traj(r)

    def _traj(self, r):
        if not bool(r.success.view(-1)[0].item()):
            return None, str(r.status)
        traj = r.get_interpolated_plan().position.view(-1, len(self.kin.names)).cpu().numpy().astype(float)
        return list(traj[1:]), None

    def approach_metric(self, p0, p, R):
        """Free motion first, then the last APPROACH_FRACTION of the trajectory a straight line into
        (p, R) along the goal-frame axis the leg follows, orientation held: the constrained form
        of a straight Cartesian leg.  None when the leg follows no TCP axis (a slanted leg has
        no axis cuRobo can hold it on)."""
        from curobo.rollout.cost.pose_cost import PoseCostMetric
        t = self.torch
        d = R.T @ (np.asarray(p, float) - np.asarray(p0, float))     # leg in the goal frame
        L = float(np.linalg.norm(d))
        axis = int(np.argmax(np.abs(d))) if L > 1e-6 else 2
        weight = [1.0] * 6
        if L > 1e-6 and abs(d[axis]) / L >= APPROACH_ALIGN:
            # cuRobo pulls the trajectory to goal - R @ offset at the start of the held part
            weight[3 + axis] = 0.0
            offset = [0.0, 0.0, 0.0]
            offset[axis] = float(d[axis]) * APPROACH_FRACTION
            return PoseCostMetric(hold_partial_pose=True,
                                  hold_vec_weight=t.tensor(weight, device="cuda", dtype=t.float32),
                                  offset_position=t.tensor(offset, device="cuda", dtype=t.float32),
                                  offset_tstep_fraction=APPROACH_FRACTION)
        return None

    def tilt_metric(self):
        """Keep the TCP's tilt (rotation about the world x / y axes) at the goal's for the whole
        trajectory; yaw and position are free.  World-frame errors (project_to_goal_frame off)."""
        from curobo.rollout.cost.pose_cost import PoseCostMetric
        t = self.torch
        return PoseCostMetric(hold_partial_pose=True, project_to_goal_frame=False,
                              hold_vec_weight=t.tensor([1.0, 1.0, 0.0, 0.0, 0.0, 0.0], device="cuda",
                                                       dtype=t.float32))

    def spheres(self, q):
        """World-frame robot spheres (x, y, z, r) at q; r < 0 for switched-off links."""
        st = self.mg.kinematics.get_state(self._js(q).position)
        return st.link_spheres_tensor.view(-1, 4)


class Motion:
    @_timed("init_s")
    def __init__(self, stage, ann, robot_cfg=ROBOT_CFG):
        import yaml
        from curobo.geom.sdf.utils import create_collision_checker
        from curobo.geom.sdf.world import CollisionCheckerType, WorldCollisionConfig
        from curobo.types.base import TensorDeviceType

        self.ann = ann
        self.cols = G.collect(stage, ann)
        body_pose = G.usd_body_pose(stage)
        world = G.to_world_config(self.cols, body_pose)
        self.checker = create_collision_checker(WorldCollisionConfig(
            TensorDeviceType(), world_model=world, checker_type=CollisionCheckerType.MESH,
            cache={"obb": len(world.cuboid) + 16, "mesh": len(world.mesh) + 8}))
        self.mesh_idx = {c.name: self.checker.get_mesh_idx(c.name) for c in self.cols.items if c.kind == "mesh"}
        G.mark_two_sided(self.checker, self.cols)
        cfg = yaml.safe_load(open(robot_cfg))["robot_cfg"]
        k = cfg["kinematics"]
        k["urdf_path"] = str(ROOT / k["urdf_path"])
        k["asset_root_path"] = str(ROOT / k["asset_root_path"])
        self.arms = {s: _Arm(self, s, cfg, self.checker) for s in ("right", "left")}
        # obstacle bookkeeping: world AABB centre / half extent per collider, start body poses
        self.body0 = {}
        self.part_q0 = {}
        for c in self.cols.items:
            if c.body is not None and c.body not in self.body0:
                self.body0[c.body] = body_pose(c.body)
        self.part_of = {a["name"]: a for a in ann.articulated}
        self.body_pose = {b: T.copy() for b, T in self.body0.items()}
        self._extent = {}
        for c in self.cols.items:
            if c.kind == "cuboid":
                h = 0.5 * np.abs(c.local[:3, :3]) @ np.asarray(c.dims, float)
                ctr = np.zeros(3)
            else:
                lo, hi = c.vertices.min(0), c.vertices.max(0)
                ctr, h = (lo + hi) / 2, (hi - lo) / 2
            self._extent[c.name] = (ctr, float(np.linalg.norm(h)))
        self.enabled = {c.name: True for c in self.cols.items}
        self.held = set()
        self.other_touching = {}     # side -> links of the other arm in contact with the world (sync)
        self.cull_at = None
        self.by_owner = {}
        for c in self.cols.items:
            self.by_owner.setdefault(c.owner, []).append(c)

    # ------------------------------------------------------------- world state
    def _centre(self, c):
        ctr, _ = self._extent[c.name]
        T = G.world_pose(c, self.body_pose.get)
        return T[:3, :3] @ ctr + T[:3, 3]

    def _set_enabled(self, c, on):
        if self.enabled[c.name] == on:
            return
        if c.kind == "mesh":
            self.checker._mesh_tensor_list[2][0, self.mesh_idx[c.name]] = (2 if c.two_sided else 1) if on else 0
        else:
            self.checker.enable_obstacle(c.name, on)
        self.enabled[c.name] = on

    def _apply(self, base_xy, allow=()):
        """Enable exactly: near the base, not held, not allowed."""
        if self.cull_at is None or np.hypot(*(np.asarray(base_xy) - self.cull_at)) > RECULL or allow:
            self.cull_at = np.asarray(base_xy, float)
        for c in self.cols.items:
            ctr = self._centre(c)
            near = np.hypot(*(ctr[:2] - self.cull_at)) - self._extent[c.name][1] < CULL
            self._set_enabled(c, near and c.owner not in self.held and c.owner not in allow)

    @_timed("sync_s")
    def sync(self, rig):
        """Object and part poses from the simulator; held objects (and what they carry) off."""
        from curobo.types.math import Pose
        t = self.arms["right"].torch
        moved = set()
        for name in self.ann.objects:
            p, q = rig.obj_pose(name)
            T = np.eye(4)
            T[:3, :3] = Rotation.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()
            T[:3, 3] = p
            body = self.ann.objects[name]["body"]
            for c in self.by_owner.get(f"object:{name}", []):
                b = c.body
                # the collider's body may be the object's body or a child of it: keep the offset
                T_b = T @ np.linalg.inv(self.body0[body]) @ self.body0[b] if body in self.body0 else T
                if not np.allclose(self.body_pose.get(b), T_b, atol=5e-4):
                    self.body_pose[b] = T_b
                    moved.add(b)
        for a in self.ann.articulated:
            q = rig.joint(a["name"])
            q0 = self.part_q0.setdefault(a["name"], q)
            M = self.ann.motion(a, q) @ np.linalg.inv(self.ann.motion(a, q0))
            for c in self.by_owner.get(f"part:{a['name']}", []):
                T_b = M @ self.body0[c.body]
                if not np.allclose(self.body_pose.get(c.body), T_b, atol=5e-4):
                    self.body_pose[c.body] = T_b
                    moved.add(c.body)
        for c in self.cols.items:
            if c.body in moved:
                T = G.world_pose(c, self.body_pose.get)
                self.checker.update_obstacle_pose(c.name, Pose.from_list(G.pose7(T)))
        held = [h["name"] for h in (rig.held, getattr(rig, "left_held", None))
                if h is not None and h.get("name") in self.ann.objects]
        self.held = set()
        for h in held:
            self.held.add(f"object:{h}")
            box = self._owner_box(f"object:{h}")
            for name in self.ann.objects:          # its contents ride along
                if name != h and self._inside(self._owner_box(f"object:{name}"), box, pad=0.02):
                    self.held.add(f"object:{name}")
        self.cull_at = None
        # links of each arm touching the world now: left out of the other arm's queries
        base = np.r_[rig.kin.base_p[:2]]
        touching = {}
        for side, kin, q, other_q in (("right", rig.kin, rig.q_cmd, np.r_[rig.q_cmd[:2], rig.left_q_cmd]),
                                      ("left", rig.left_kin, np.r_[rig.q_cmd[:2], rig.left_q_cmd], rig.q_cmd)):
            arm = self.arms[side]
            arm.prepare(kin, other_q, {f"{side}_{l}" for l in FINGER_LINKS})
            self._apply(base)
            touching[side] = {l for l in self._touching(arm, q) if l.startswith(side + "_")}
        self.other_touching = {"right": touching["left"], "left": touching["right"]}
        self.cull_at = None

    def _owner_box(self, owner):
        P = []
        for c in self.by_owner.get(owner, []):
            ctr = self._centre(c)
            r = self._extent[c.name][1]
            P += [ctr - r, ctr + r]
        P = np.array(P) if P else np.zeros((2, 3))
        return P.min(0), P.max(0)

    @staticmethod
    def _inside(a, b, pad=0.0):
        ca = (a[0] + a[1]) / 2
        return bool(np.all(ca > b[0] - pad) and np.all(ca < b[1] + pad))

    def _targets_allow(self, points):
        """Objects whose box (+TARGET_PAD) contains one of the TCP targets."""
        out = set()
        for owner in self.by_owner:
            if not owner.startswith("object:"):
                continue
            lo, hi = self._owner_box(owner)
            for p in points:
                if np.all(p > lo - TARGET_PAD) and np.all(p < hi + TARGET_PAD):
                    out.add(owner)
        return out

    @contextmanager
    def _query(self, kin, other_q=None, coll_kw=None, targets=(), collision=True):
        coll_kw = coll_kw or {}
        own = HAND_LINKS if coll_kw.get("hand_touches_part") else FINGER_LINKS if coll_kw.get("ignore_fingers") else ()
        other = "left" if kin.side == "right" else "right"
        # the other arm is fixed for this query: its fingers (never checked against this arm)
        # and whatever of it already touches the world (a hand holding a handle) stay out
        links = {f"{kin.side}_{l}" for l in own} | {f"{other}_{l}" for l in FINGER_LINKS} | \
            self.other_touching.get(kin.side, set())
        arm = self.arms[kin.side]
        arm.prepare(kin, other_q, links)
        if collision:
            self._apply(kin.base_p[:2], allow=self._targets_allow([np.asarray(p, float) for p in targets]))
        try:
            yield arm
        finally:
            if collision and targets:
                self.cull_at = None          # the allowed targets go back on at the next query

    # ------------------------------------------------------------- API (kinematics.ArmKin)
    @_timed("ik_s")
    def ik(self, kin, p, R, seeds, collision, other_q=None, coll_kw=None, local=False):
        STATS["ik"] += 1
        with self._query(kin, other_q, coll_kw, [p], collision) as arm:
            # kinematic IK first (cheap): most failures are out of reach, and a kinematic answer
            # that is already collision-free needs no world-aware solve
            q, ok = arm.ik(p, R, seeds, False, local)
            if collision and not ok:
                STATS["ik_fail_reach"] = STATS.get("ik_fail_reach", 0) + 1
            elif collision and not arm.feasible(q[None])[0]:
                qf = q
                q, ok = arm.ik(p, R, [qf] + list(seeds), True, local)
                if not ok:
                    STATS["ik_fail_collision"] = STATS.get("ik_fail_collision", 0) + 1
                    if DIAG and STATS["ik_fail_collision"] <= 40:
                        print(f"[motion] {kin.side} IK blocked at {np.round(p, 3).tolist()}: "
                              f"{self._explain(arm, qf)}", flush=True)
        STATS["ik_ok"] += int(ok)
        return q, ok

    @_timed("cart_s")
    def cart_path(self, kin, q0, p_goal, R_goal, step, collision, other_q=None, coll_kw=None):
        """Straight TCP line (slerp orientation) as cuRobo IK solutions (batched, see
        _Arm.path_ik); continuous (<= MAX_STEP rad per joint between waypoints) and, with
        collision, every waypoint and the joint segments between them feasible."""
        from scipy.spatial.transform import Slerp
        STATS["cart"] += 1
        p0, R0 = kin.tcp(q0)
        n = max(2, int(np.ceil(np.linalg.norm(p_goal - p0) / step)) + 1)
        ang = np.linalg.norm(Rotation.from_matrix(R_goal @ R0.T).as_rotvec())
        n = max(n, int(np.ceil(ang / 0.05)) + 1)
        slerp = Slerp([0, 1], Rotation.from_matrix([R0, R_goal]))
        us = np.linspace(0, 1, n)[1:]
        with self._query(kin, other_q, coll_kw, [p0, p_goal], collision) as arm:
            out, ok = arm.path_ik([p0 + (p_goal - p0) * u for u in us], [slerp(u).as_matrix() for u in us], q0)
            if not ok:
                return out, False
            if collision and not self._segments_free(arm, [np.asarray(q0, float)] + out):
                return out, False
        STATS["cart_ok"] += 1
        return out, True

    def _segments_free(self, arm, qs, res=0.05):
        dense = []
        for qa, qb in zip(qs[:-1], qs[1:]):
            k = max(1, int(np.max(np.abs(qb - qa)) / res))
            dense += [qa + (qb - qa) * u for u in np.linspace(0, 1, k + 1)[1:]]
        return bool(arm.feasible(np.array(dense)).all())

    @_timed("check_s")
    def free(self, kin, q, other_q=None, coll_kw=None):
        STATS["check"] += 1
        with self._query(kin, other_q, coll_kw) as arm:
            return bool(arm.feasible(np.asarray(q, float)[None])[0])

    @_timed("check_s")
    def segment_free(self, kin, qa, qb, other_q=None, coll_kw=None):
        STATS["check"] += 1
        with self._query(kin, other_q, coll_kw) as arm:
            return self._segments_free(arm, [np.asarray(qa, float), np.asarray(qb, float)])

    @_timed("plan_s")
    def plan(self, kin, q0, q1, other_q=None, coll_kw=None, carry=False):
        """cuRobo joint-space trajectory q0 -> q1 (waypoints after q0) or (None, status).
        ``carry`` (an object in the hand): the held object may not tilt more than CARRY_TILT
        on the way; a trajectory that would is re-planned to q1's TCP pose with the tilt held
        (it then ends at that pose, not necessarily at q1)."""
        STATS["plan"] += 1
        q0, q1 = np.asarray(q0, float), np.asarray(q1, float)
        with self._query(kin, other_q, coll_kw) as arm:
            qs, status = arm.plan(q0, q1)
            R0 = kin.tcp(q0)[1]
            p1, R1 = kin.tcp(q1)
            if carry and tilt(R0, R1) <= CARRY_TILT and (qs is None or max_tilt(kin, R0, qs) > CARRY_TILT):
                STATS["plan_carry"] = STATS.get("plan_carry", 0) + 1
                qc, sc = arm.plan_pose(q0, p1, R1, arm.tilt_metric())
                if qc is not None and max_tilt(kin, R0, qc) <= CARRY_TILT:
                    qs, status = qc, None
                else:
                    qs, status = None, f"carry tilt held: {sc or 'tilts %.2f rad' % max_tilt(kin, R0, qc)}"
        STATS["plan_ok"] += int(qs is not None)
        return qs, status

    @_timed("plan_s")
    def plan_to(self, kin, q0, p0, p, R, other_q=None, coll_kw=None, carry=False):
        """Constrained trajectory for a Cartesian leg p0 -> (p, R) whose straight line is blocked:
        with an object in the hand the tilt is held throughout; otherwise the trajectory may
        leave the line to clear the obstacle but ends with a straight approach along it
        (Arm.approach_metric).  (qs, None) or (None, status)."""
        STATS["plan_to"] = STATS.get("plan_to", 0) + 1
        q0 = np.asarray(q0, float)
        with self._query(kin, other_q, coll_kw, [p0, p]) as arm:
            R0 = kin.tcp(q0)[1]
            if carry and tilt(R0, R) <= CARRY_TILT:
                metric = arm.tilt_metric()
            else:
                metric = arm.approach_metric(p0, p, R)
            if metric is None:
                return None, "leg follows no TCP axis: no constrained approach"
            qs, status = arm.plan_pose(q0, np.asarray(p, float), R, metric)
            if qs is not None and carry and max_tilt(kin, R0, qs) > CARRY_TILT + tilt(R0, R):
                qs, status = None, "held object tilts on the planned leg"
        STATS["plan_to_ok"] = STATS.get("plan_to_ok", 0) + int(qs is not None)
        return qs, status

    def _touching(self, arm, q):
        """{link: depth} of the robot's links penetrating the world at q."""
        import torch
        from curobo.geom.sdf.world import CollisionQueryBuffer
        sph = arm.spheres(np.asarray(q, float))
        kc = arm.kcs[0]
        idx = kc.link_sphere_idx_map.cpu().numpy()
        by_idx = {v: k for k, v in kc.link_name_to_idx_map.items()}
        q4 = sph.view(1, 1, -1, 4).contiguous()
        buf = CollisionQueryBuffer.initialize_from_shape(q4.shape, arm.mg.tensor_args, self.checker.collision_types)
        d = self.checker.get_sphere_distance(q4, buf, torch.ones(1, device="cuda"), torch.zeros(1, device="cuda"),
                                             sum_collisions=False).view(-1).cpu().numpy()
        r = sph[:, 3].cpu().numpy()
        hits = {}
        for i in np.nonzero((d > 0) & (r > 0))[0]:
            link = by_idx.get(int(idx[i]), str(idx[i]))
            hits[link] = max(hits.get(link, 0.0), float(d[i]))
        return hits

    def _explain(self, arm, q):
        """Which links of q penetrate the world (deepest first), else self collision / limits."""
        hits = self._touching(arm, q)
        if hits:
            return "world " + ", ".join(f"{l} {v * 1000:.0f} mm" for l, v in
                                        sorted(hits.items(), key=lambda t: -t[1])[:4])
        return "self collision or joint limits"

    @_timed("check_s")
    def clearance(self, kin, Q, targets=(), other_q=None, coll_kw=None):
        """Per row of Q: the arm's smallest distance to the world (m, capped at CLEAR_CAP; 0 when
        touching): spheres inflated by CLEAR_CAP, minus their deepest penetration.  Fingers and
        the objects at the TCP ``targets`` are left out (they are meant to touch)."""
        import torch
        from curobo.geom.sdf.world import CollisionQueryBuffer
        STATS["check"] += 1
        Q = np.atleast_2d(np.asarray(Q, float))
        kw = dict(coll_kw or {})
        if not kw.get("hand_touches_part"):
            kw["ignore_fingers"] = True
        with self._query(kin, other_q, kw, [np.asarray(p, float) for p in targets]) as arm:
            sph = arm.spheres(np.clip(Q, arm.lo, arm.hi)).view(len(Q), -1, 4).clone()
            on = sph[..., 3] > 0
            sph[..., 3] = torch.where(on, sph[..., 3] + CLEAR_CAP, sph[..., 3])
            q4 = sph.view(len(Q), 1, -1, 4).contiguous()
            buf = CollisionQueryBuffer.initialize_from_shape(q4.shape, arm.mg.tensor_args,
                                                             self.checker.collision_types)
            d = self.checker.get_sphere_distance(q4, buf, torch.ones(1, device="cuda"),
                                                 torch.zeros(1, device="cuda"), sum_collisions=False)
            d = torch.where(on, d.view(len(Q), -1), torch.zeros_like(on, dtype=d.dtype))
            pen = d.max(dim=1).values.cpu().numpy()
        return np.clip(CLEAR_CAP - pen, 0.0, CLEAR_CAP)

    def penetration(self, kin, q, other_q=None, coll_kw=None):
        """Deepest penetration (m, >= 0) of the robot's spheres into the world at q."""
        import torch
        from curobo.geom.sdf.world import CollisionQueryBuffer
        with self._query(kin, other_q, coll_kw) as arm:
            sph = arm.spheres(np.asarray(q, float))
            sph = sph[sph[:, 3] > 0].view(1, 1, -1, 4).contiguous()
            buf = CollisionQueryBuffer.initialize_from_shape(sph.shape, arm.mg.tensor_args,
                                                             self.checker.collision_types)
            d = self.checker.get_sphere_distance(sph, buf, torch.ones(1, device="cuda"),
                                                 torch.zeros(1, device="cuda"), sum_collisions=False)
            return float(d.max().item()) if d.numel() else 0.0
