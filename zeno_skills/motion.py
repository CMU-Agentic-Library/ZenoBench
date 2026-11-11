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
  * loose objects are obstacles; an object a hand holds (and what it carries) is
    not, to that arm (to the other arm only while its hand is at it: a handover);
    nor is an object whose box (+3 cm) contains a query's TCP target (the
    object being grasped or pushed);
  * inside ``scope`` (every collision-checked rig motion, Rig._planning) the held object is a
    grid of spheres filling its box on the arm's ``<side>_held_object`` link: the planner keeps
    it clear of the world (never of the robot itself).  Not while it still touches something;
  * ``ignore_fingers`` turns the finger spheres off; ``hand_touches_part`` the
    finger, gripper and wrist-camera spheres (hand on a handle; the old skills set it against
    the whole world -- Motion.query takes a Spec.touch / a held part instead, against that only);
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
from .kinematics import CARRY_TILT, manipulability, max_tilt, tilt, tips_over
from .motion_state import touch_entries, touches

ROOT = Path(__file__).resolve().parents[1]
ROBOT_CFG = ROOT / "robot_sources/curobo/zeno_malo.yml"
BASE_JOINTS = ("base_x", "base_y", "base_yaw")
CULL = 2.5                 # obstacles beyond this (xy, from the base) are off
MONITOR_NEAR = 1.6         # contact monitor: objects and parts this close (xy, from the base) are re-posed
RECULL = 0.4               # re-cull when the query base moved this far
HAND_AT_HELD = 0.05       # a hand this close (TCP to box) to what the other hand holds: not an obstacle to it
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
TRAJOPT_SEEDS = 6         # trajectory-optimisation seeds per plan (fixed: CUDA graph shape)
GRAPH_SEEDS = 2           # graph-search seeds that seed the optimiser around obstacles
# The seeds size the planner's working buffers, which a process keeps from its first plan: 12 / 4
# peaked at 13.2 GB of a 24 GB card in a full episode, 6 / 2 at 10.3 GB (obstacle count does not
# matter, an empty world costs 182 MB either way).
PLAN_ATTEMPTS, PLAN_TIMEOUT = 5, 8.0
APPROACH_FRACTION = 0.5   # constrained Cartesian legs: the last half of the trajectory is the straight approach
APPROACH_ALIGN = 0.95     # |cos| between the leg and a goal-frame axis for a straight-approach constraint
HELD_SPHERES = 32         # spheres pre-allocated per arm for the held object (scope)
COARSE_STEP = 0.02        # m: a finer Cartesian line that fails is solved again at this step, then densified
BASE_CHUNK = 2048         # base poses per batched whole-body query (base_depths)
os.environ.setdefault("CUROBO_TORCH_CUDA_GRAPH_RESET", "1")

DIAG = os.environ.get("ZENO_MOTION_DIAG") == "1"     # print why a collision IK was blocked
STATS = {"ik": 0, "ik_ok": 0, "cart": 0, "cart_ok": 0, "plan": 0, "plan_ok": 0, "check": 0,
         "ik_s": 0.0, "cart_s": 0.0, "plan_s": 0.0, "check_s": 0.0, "sync_s": 0.0, "init_s": 0.0,
         "monitor_s": 0.0, "base_s": 0.0}


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


def held_link(side):
    return f"{side}_held_object"


def load(rig, side):
    """What ``side``'s hand carries for the collision model: what it holds, else the object it
    is lifting before that counts as held (Rig._lifting)."""
    h = rig.held if side == "right" else getattr(rig, "left_held", None)
    return h if h is not None else getattr(rig, "lifting", {}).get(side)


def add_held_links(k):
    """Robot config (the ``kinematics`` dict) + one empty sphere link per arm at its TCP for
    the held object: HELD_SPHERES spheres switched off until attached, never in self collision."""
    k["extra_links"] = dict(k["extra_links"])
    links = list(k["collision_link_names"])
    for s in ("right", "left"):
        tcp = k["extra_links"][f"{s}_tcp"]
        k["extra_links"][held_link(s)] = {**tcp, "link_name": held_link(s), "joint_name": f"{held_link(s)}_joint"}
    held = [held_link(s) for s in ("right", "left")]
    k["collision_link_names"] = links + held
    k["extra_collision_spheres"] = {h: HELD_SPHERES for h in held}
    k["self_collision_ignore"] = {**k.get("self_collision_ignore", {}),
                                  **{h: [l for l in links + held if l != h] for h in held}}
    k["self_collision_buffer"] = {**k.get("self_collision_buffer", {}), **{h: 0.0 for h in held}}
    return k


def box_spheres(lo, hi, n_max=HELD_SPHERES):
    """(n, 4) equal spheres (x, y, z, r) on a grid filling the box [lo, hi]: cells as close to
    cubes as n_max allows, each sphere inscribed in its cell (inside the box)."""
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    d = np.maximum(hi - lo, 1e-3)
    r = d.min() / 2
    while True:
        n = np.maximum(1, np.ceil(d / (2 * r) - 1e-9)).astype(int)
        if n.prod() <= n_max:
            break
        r *= 1.1
    cell = d / n
    idx = np.stack(np.meshgrid(*[np.arange(k) for k in n], indexing="ij"), -1).reshape(-1, 3)
    ctr = lo + (idx + 0.5) * cell
    return np.c_[ctr, np.full(len(ctr), cell.min() / 2)]


class _Locks:
    """In-place rewrite of locked joints' fixed transforms (cuRobo's own
    update_locked_joints re-parses the URDF: seconds per call).  A joint that mimics a locked one
    (a gripper's right finger mimics its left finger axis) is locked with it: cuRobo fixed it at
    its leader's lock value, and it follows the leader's value (multiplier * v + offset) unless
    ``set`` is given its own."""

    def __init__(self, models, lock, urdf):
        joints = {j.get("name"): j for j in ET.parse(urdf).getroot().findall("joint")}
        self.models = []
        for m in models:
            kc = m.kinematics_config
            if all(kc.fixed_transforms.data_ptr() != x.fixed_transforms.data_ptr() for x in self.models):
                self.models.append(kc)
        self.entries, self.values, self.followers = {}, {}, {}
        for name, v0 in lock.items():
            self._entry(joints[name], v0)
            for j in joints.values():
                m = j.find("mimic")
                if m is not None and m.get("joint") == name:
                    mult, off = float(m.get("multiplier", 1.0)), float(m.get("offset", 0.0))
                    self._entry(j, mult * v0 + off)
                    self.followers.setdefault(name, []).append((j.get("name"), mult, off))

    def _entry(self, j, v0):
        name = j.get("name")
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
        self.values[name] = float(v0)

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
        values = dict(values)
        for name, fs in self.followers.items():
            if name in values:
                for f, mult, off in fs:
                    values.setdefault(f, mult * float(values[name]) + off)
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
    def prepare(self, kin, other_q, links_off, live=None):
        """Locks (base pose, other arm; ``live``: the head and finger joints where the robot has
        them), joint limits (kin.lo / kin.hi: skills cap the waist or pin the torso) and
        switched-off links for the next query."""
        yaw = math.atan2(kin.base_R[1, 0], kin.base_R[0, 0])
        vals = {"base_x": kin.base_p[0], "base_y": kin.base_p[1], "base_yaw": yaw}
        if other_q is not None:
            vals.update(zip(self.other_names, np.asarray(other_q, float)[-len(self.other_names):]))
        vals.update(live or {})
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

    def ik_batch(self, P, Rs, q0, collision):
        """Every IK solution of each TCP pose (P[i], Rs[i]), seeded with and regularised towards
        q0, in batched calls (PATH_BATCH per call, padded: fixed CUDA graph shape); with
        ``collision`` the world-aware solver.  (Q (n, N_RETURN, dof), ok (n, N_RETURN)), ok inside
        the limits."""
        from curobo.types.math import Pose
        t = self.torch
        n_dof = len(self.kin.names)
        q0 = np.clip(np.asarray(q0, float), self.lo, self.hi)
        solver = self.mg.ik_solver if collision else self.ik_path
        Qs, oks = [], []
        for c in range(0, len(P), PATH_BATCH):
            Pc, Rc = list(P[c:c + PATH_BATCH]), list(Rs[c:c + PATH_BATCH])
            k = len(Pc)
            pos = np.array(Pc + [Pc[-1]] * (PATH_BATCH - k), np.float32)
            quat = np.array([_quat_wxyz(R) for R in Rc + [Rc[-1]] * (PATH_BATCH - k)], np.float32)
            seed = t.as_tensor(np.tile(q0.astype(np.float32), (PATH_BATCH, N_SEEDS, 1)), device="cuda")
            retract = t.as_tensor(np.tile(q0.astype(np.float32), (PATH_BATCH, 1)), device="cuda")
            r = solver.solve_batch(Pose(t.as_tensor(pos, device="cuda"), t.as_tensor(quat, device="cuda")),
                                   retract_config=retract, seed_config=seed, return_seeds=N_RETURN)
            Q = r.solution.view(PATH_BATCH, -1, n_dof).cpu().numpy().astype(float)[:k]
            ok = r.success.view(PATH_BATCH, -1).cpu().numpy().astype(bool)[:k]
            ok &= np.all((Q >= self.lo - 1e-4) & (Q <= self.hi + 1e-4), axis=2)
            Qs.append(Q)
            oks.append(ok)
        return np.concatenate(Qs), np.concatenate(oks)

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


SIDES_ = ("right", "left")


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
        add_held_links(k)
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
        self._corners = {c.name: self.box_corners(c) for c in self.cols.items}
        for c in self.cols.items:
            if c.kind == "cuboid":
                h = 0.5 * np.abs(c.local[:3, :3]) @ np.asarray(c.dims, float)
                ctr = np.zeros(3)
            else:
                lo, hi = c.vertices.min(0), c.vertices.max(0)
                ctr, h = (lo + hi) / 2, (hi - lo) / 2
            self._extent[c.name] = (ctr, float(np.linalg.norm(h)))
        self.enabled = {c.name: True for c in self.cols.items}
        self.held = {"right": set(), "left": set()}     # side -> owners that arm holds (not obstacles to it)
        self._held_sph = {}              # side -> spheres of the held object on its held link (scope), or None
        self._held_box = {}              # object name -> (frame collider, lo, hi): its box in that collider's frame
        self.other_touching = {}     # side -> links of the other arm in contact with the world (sync)
        self.cull_at = None
        self.exempt = []                 # objects the last query left out as targets (_targets_allow)
        self.hand_width = {}             # side -> finger opening the queries take (hand_open), else the robot's
        self.relaxed = {}                # side -> what its collision queries left out since the motion
                                         # record last took it (take_relaxed): "exempt", "fingers", "hand"
        self._sync_n = 0
        self._base_scope = None
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

    def _apply(self, base_xy, allow=(), side="right"):
        """Enable exactly: near the base, not held by the ``side`` arm, not allowed."""
        if self.cull_at is None or np.hypot(*(np.asarray(base_xy) - self.cull_at)) > RECULL or allow:
            self.cull_at = np.asarray(base_xy, float)
        held = self.held[side]
        for c in self.cols.items:
            ctr = self._centre(c)
            near = np.hypot(*(ctr[:2] - self.cull_at)) - self._extent[c.name][1] < CULL
            self._set_enabled(c, near and c.owner not in held and c.owner not in allow)

    def _live_poses(self, rig, record=True, owners=None):
        """{body: 4x4} of the object and part bodies whose simulator pose differs from the synced
        one (only ``owners``' when given).  ``record``: the first look at a part fixes its
        reference joint value (sync only)."""
        out = {}
        for name in self.ann.objects:
            if owners is not None and f"object:{name}" not in owners:
                continue
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
                    out[b] = T_b
        for a in self.ann.articulated:
            if owners is not None and f"part:{a['name']}" not in owners:
                continue
            q = rig.joint(a["name"])
            q0 = self.part_q0.setdefault(a["name"], q) if record else self.part_q0.get(a["name"], q)
            M = self.ann.motion(a, q) @ np.linalg.inv(self.ann.motion(a, q0))
            for c in self.by_owner.get(f"part:{a['name']}", []):
                T_b = M @ self.body0[c.body]
                if not np.allclose(self.body_pose.get(c.body), T_b, atol=5e-4):
                    out[c.body] = T_b
        return out

    def _put_poses(self, poses):
        """cuRobo obstacles of the bodies in ``poses`` to those poses (the rest unchanged)."""
        from curobo.types.math import Pose
        if not poses:
            return
        if not hasattr(self, "_cols_of_body"):
            self._cols_of_body = {}
            for c in self.cols.items:
                self._cols_of_body.setdefault(c.body, []).append(c)
        at = lambda b: poses[b] if b in poses else self.body_pose.get(b)
        for b in poses:
            for c in self._cols_of_body.get(b, ()):
                self.checker.update_obstacle_pose(c.name, Pose.from_list(G.pose7(G.world_pose(c, at))))

    @_timed("sync_s")
    def sync(self, rig):
        """Object and part poses from the simulator; held objects (and what they carry) off."""
        self.rig = rig
        self._sync_n = getattr(self, "_sync_n", 0) + 1
        moved = self._live_poses(rig)
        self.body_pose.update(moved)
        self._put_poses(moved)
        # what a hand holds (and its contents) is not an obstacle to that arm; to the other arm
        # it is, unless that hand is at it too (a handover, a two-hand hold)
        self.held = {"right": set(), "left": set()}
        for side, h in (("right", load(rig, "right")), ("left", load(rig, "left"))):
            if h is None or h.get("name") not in self.ann.objects:
                continue
            owners = self._held_owners(h["name"])
            for s_ in (("right", "left") if h.get("kind") == "bimanual" else (side,)):
                self.held[s_] |= owners
        for side, kin, q in (("right", rig.kin, rig.q_cmd), ("left", rig.left_kin, np.r_[rig.q_cmd[:2], rig.left_q_cmd])):
            tcp = kin.tcp(np.asarray(q, float))[0]
            for o in self.held["left" if side == "right" else "right"] - self.held[side]:
                lo, hi = self._owner_box(o)
                if np.all(tcp > lo - HAND_AT_HELD) and np.all(tcp < hi + HAND_AT_HELD):
                    self.held[side].add(o)
        self.cull_at = None
        # links of each arm touching the world now: left out of the other arm's queries
        base = np.r_[rig.kin.base_p[:2]]
        touching = {}
        for side, kin, q, other_q in (("right", rig.kin, rig.q_cmd, np.r_[rig.q_cmd[:2], rig.left_q_cmd]),
                                      ("left", rig.left_kin, np.r_[rig.q_cmd[:2], rig.left_q_cmd], rig.q_cmd)):
            arm = self.arms[side]
            arm.prepare(kin, other_q, {f"{side}_{l}" for l in FINGER_LINKS}, self.live_locks())
            self._apply(base, side=side)
            hits = self._touching(arm, q)
            touching[side] = {l for l in hits if l.startswith(side + "_") and l != held_link(side)}
        self.other_touching = {"right": touching["left"], "left": touching["right"]}
        self.cull_at = None

    def live_locks(self):
        """{locked joint: value} of the head and the fingers as the robot has them now: a hand
        closed on a load is not the open hand of the robot config (the planner had the fingers
        at FINGER_OPEN, 2.5 cm wider each side than a pinched spoon, and the tilt-held carry of
        T03 ran that phantom finger into the island).  The second finger mimics the first; the
        wider of the two is taken."""
        from .kinematics import FINGER_OPEN
        rig = getattr(self, "rig", None)
        vals = {}
        if rig is None:
            return vals
        if getattr(self, "head_override", None) is not None:
            vals.update(self.head_override)
        elif hasattr(rig, "head_q"):
            vals.update(rig.head_q())
        for side, read in (("right", "fingers"), ("left", "left_fingers")):
            if side in self.hand_width:
                vals[f"{side}_gripper_left_finger_axis"] = self.hand_width[side]
            elif hasattr(rig, read):
                f = np.asarray(getattr(rig, read)(), float)[:2]
                vals[f"{side}_gripper_left_finger_axis"] = float(np.clip(f.max(), 0.0, FINGER_OPEN))
        return vals

    @contextmanager
    def hand_open(self, side, width):
        """Queries inside take ``side``'s fingers at ``width`` (m per finger) instead of where they
        stand: a park search for a grasp checks the hand opened as it will approach."""
        saved = dict(self.hand_width)
        self.hand_width[side] = float(width)
        try:
            yield
        finally:
            self.hand_width = saved

    @contextmanager
    def scope(self, rig, kin, q, keep_held=False):
        """One collision-checked rig motion of ``kin``'s arm from q (Rig._planning): what that hand
        holds is in the arm's collision model, its box as spheres on the held link (left out, and
        logged, while it still touches something at q -- unless ``keep_held``: the exit out of a
        contact asks when the load comes clear too)."""
        side = kin.side
        h = load(rig, side)
        q = np.asarray(q, float)
        try:
            with self._query(kin, kin._other_q(), kin.coll_kw) as arm:
                name = self._attach_held(arm, kin, q, h)
                if name is not None and not keep_held and held_link(side) in self._touching(arm, q):
                    # still on its support (or in a container): no collision-free start, left out
                    self._attach_held(arm, kin, q, None)
                    rig.log("held_collision", side=side, state=f"{name} (touching: off)")
            yield
        finally:
            self._attach_held(self.arms[side], None, None, None)
            self.cull_at = None

    def held_in_tcp(self, kin, q, name):
        """4x4 of ``name``'s box frame (_box_of) in ``kin``'s TCP frame at q, both at their synced
        poses: how the hand holds it.  Taken at the real base, it stays valid for a park search
        that moves the base (carrying, released)."""
        frame, _, _ = self._box_of(name)
        p, R = kin.tcp(np.asarray(q, float))
        T_tcp = np.eye(4)
        T_tcp[:3, :3], T_tcp[:3, 3] = R, p
        return np.linalg.inv(T_tcp) @ G.world_pose(frame, self.body_pose.get)

    def _attach_held(self, arm, kin, q, h):
        """Spheres of the held object ``h`` (box_spheres of its box, in the TCP frame at q) on
        the arm's held link; None (or a bimanual hold): the link emptied.  Returns the name."""
        name = None if h is None or h.get("kind") == "bimanual" else h.get("name")
        if name is None or not self.by_owner.get(f"object:{name}"):
            self._attach_rel(arm, None, None)
            return None
        self._attach_rel(arm, name, self.held_in_tcp(kin, q, name))
        return name

    def _attach_rel(self, arm, name, M, pad=0.0):
        """Spheres of ``name``'s box on the arm's held link, the box frame at M in the TCP frame
        (held_in_tcp), their radii ``pad`` larger; None: the link emptied."""
        sph = None
        if name is not None:
            _, lo, hi = self._box_of(name)
            b = box_spheres(lo, hi)
            sph = np.full((HELD_SPHERES, 4), [0.0, 0.0, 0.0, -100.0])
            sph[:len(b), :3] = b[:, :3] @ M[:3, :3].T + M[:3, 3]
            sph[:len(b), 3] = b[:, 3] + pad
        if sph is not None or self._held_sph.get(arm.side) is not None:
            self._set_held_spheres(arm, sph)
        self._held_sph[arm.side] = sph

    @contextmanager
    def carrying(self, side, name, M):
        """Queries inside take ``side``'s hand holding ``name`` with its box frame at M in the TCP
        frame (held_in_tcp): a park search checks the legs of a place with the load in the hand,
        as Rig._planning (scope) has it when they are executed."""
        arm = self.arms[side]
        self._attach_rel(arm, name, M)
        try:
            yield
        finally:
            self._attach_rel(arm, None, None)
            self.cull_at = None

    @contextmanager
    def empty_hand(self, side):
        """Queries inside take ``side``'s hand empty, what it held gone (a drop: let go in the air,
        it falls into the container, out of the way of the hand's tuck)."""
        sph = self._held_sph.get(side)
        self._attach_rel(self.arms[side], None, None)
        try:
            yield
        finally:
            if sph is not None:
                self._set_held_spheres(self.arms[side], sph)
                self._held_sph[side] = sph
            self.cull_at = None

    @contextmanager
    def released(self, side, name, T_frame):
        """Queries inside take ``name`` let go by ``side``'s hand: an obstacle with its box frame
        (_box_of) at the world pose T_frame (where the place sets it down), the hand empty.  A park
        search checks what follows the release (the pull-out, the tuck) as it will be executed."""
        owner = f"object:{name}"
        frame, _, _ = self._box_of(name)
        D = np.asarray(T_frame, float) @ np.linalg.inv(G.world_pose(frame, self.body_pose.get))
        bodies = {c.body for c in self.by_owner.get(owner, [])}
        saved = {b: self.body_pose.get(b) for b in bodies}
        held = self.held[side]
        sph = self._held_sph.get(side)
        moved = {b: D @ T for b, T in saved.items() if T is not None}
        self.body_pose.update(moved)
        self._put_poses(moved)
        self.held[side] = held - {owner}
        self._attach_rel(self.arms[side], None, None)
        self.cull_at = None
        try:
            yield
        finally:
            self.body_pose.update({b: T for b, T in saved.items() if T is not None})
            self._put_poses({b: T for b, T in saved.items() if T is not None})
            self.held[side] = held
            if sph is not None:
                self._set_held_spheres(self.arms[side], sph)
                self._held_sph[side] = sph
            self.cull_at = None

    def _held_owners(self, name):
        """The owners a hand holding ``name`` carries: it and what is inside its box (its contents)."""
        owners = {f"object:{name}"}
        box = self._owner_box(f"object:{name}")
        for other in self.ann.objects:
            if other != name and self._inside(self._owner_box(f"object:{other}"), box, pad=0.02):
                owners.add(f"object:{other}")
        return owners

    def object_frames(self):
        """{name: 4x4 world pose of its box frame (_box_of)} at the synced poses (State.objects)."""
        out = {}
        for name in self.ann.objects:
            if self.by_owner.get(f"object:{name}"):
                frame, _, _ = self._box_of(name)
                out[name] = G.world_pose(frame, self.body_pose.get)
        return out

    def _part_poses(self, name, q):
        """{body: 4x4} of part ``name``'s colliders at joint value q (as _live_poses)."""
        a = next(a for a in self.ann.articulated if a["name"] == name)
        q0 = self.part_q0.get(name, q)
        M = self.ann.motion(a, q) @ np.linalg.inv(self.ann.motion(a, q0))
        return {c.body: M @ self.body0[c.body] for c in self.by_owner.get(f"part:{name}", [])}

    @contextmanager
    def query(self, kin, state, spec):
        """Queries of ``kin``'s arm inside take the world and the robot as ``state`` has them and
        the collision rules of ``spec`` (docs/MOTION_ARCHITECTURE.md 4.4): the base, the other
        arm, the head and finger locks, what each hand holds (on its held link, not an obstacle to
        it), objects and parts where the state puts them, and kin.coll_kw from the spec.  Only
        what differs from the synced world is changed, and everything is put back after.  The
        first form over the per-purpose contexts (hand_open, carrying, released, scope)."""
        side = kin.side
        other_attr = "left_q" if side == "right" else "right_q"
        scene = kin.scene
        saved = {"base": (kin.base_p.copy(), kin.base_R.copy()), "kw": kin.coll_kw,
                 "touch": getattr(self, "finger_touch", set()),
                 "other": getattr(scene, other_attr, None) if scene is not None else None,
                 "width": dict(self.hand_width), "head": getattr(self, "head_override", None),
                 "held": {s_: set(v) for s_, v in self.held.items()},
                 "sph": dict(self._held_sph)}
        moved = {}
        try:
            x, y, yaw = state.base
            kin.set_base((x, y, 0.0), math.radians(yaw))
            if scene is not None:
                setattr(scene, other_attr, np.r_[np.asarray(state.q_right, float)[:2], state.q_left]
                        if side == "right" else np.asarray(state.q_right, float))
            self.hand_width = {s_: h.width for s_, h in state.hands.items()}
            self.head_override = dict(state.head) if state.head else None
            kw = {k: v for k, v in (kin.coll_kw or {}).items() if k not in ("ignore_fingers", "exempt_targets")}
            kw["ignore_fingers"] = not spec.fingers
            kw["exempt_targets"] = bool(spec.exempt)
            kin.coll_kw = kw
            # what the hand may touch (Spec.touch and a part it holds): no obstacle in these queries;
            # path_free_only checks the rest of the arm against them apart
            self.finger_touch = {self.touch_owner(n) for n, _ in touches(state, spec, side)}
            # objects and parts the state has elsewhere than the synced world
            for name, T in state.objects.items():
                owner = f"object:{name}"
                if not self.by_owner.get(owner):
                    continue
                frame, _, _ = self._box_of(name)
                T0 = G.world_pose(frame, self.body_pose.get)
                if np.allclose(T0, T, atol=1e-6):
                    continue
                D = np.asarray(T, float) @ np.linalg.inv(T0)
                for b in {c.body for c in self.by_owner[owner]}:
                    if self.body_pose.get(b) is not None:
                        moved.setdefault(b, self.body_pose.get(b))
                        self.body_pose.update({b: D @ self.body_pose.get(b)})
            for name, q in state.parts.items():
                if not self.by_owner.get(f"part:{name}"):
                    continue
                for b, T_b in self._part_poses(name, q).items():
                    if not np.allclose(self.body_pose.get(b), T_b, atol=1e-6):
                        moved.setdefault(b, self.body_pose.get(b))
                        self.body_pose.update({b: T_b})
            self._put_poses({b: self.body_pose.get(b) for b in moved})
            # what each hand holds: not an obstacle to that arm, its box on the held link
            for s_ in SIDES_:
                h = state.held(s_)
                was = saved["held"].get(s_, set())
                sim = load(self.rig, s_) if getattr(self, "rig", None) is not None else None
                sim_owners = self._held_owners(sim["name"]) if sim and sim.get("name") in self.ann.objects else set()
                if h is None or h.kind == "part":       # a handle held: nothing rides on the hand (touches)
                    self.held[s_] = was - sim_owners
                    self._attach_rel(self.arms[s_], None, None)
                else:
                    self.held[s_] = (was - sim_owners) | self._held_owners(h.name)
                    if h.kind != "bimanual" and self.by_owner.get(f"object:{h.name}"):
                        self._attach_rel(self.arms[s_], h.name, np.asarray(h.T_tcp_obj, float), h.pad)
                    else:
                        self._attach_rel(self.arms[s_], None, None)
            self.cull_at = None
            yield
        finally:
            kin.base_p, kin.base_R = saved["base"]
            kin.coll_kw = saved["kw"]
            self.finger_touch = saved["touch"]
            if scene is not None:
                setattr(scene, other_attr, saved["other"])
            self.hand_width = saved["width"]
            self.head_override = saved["head"]
            self.held = saved["held"]
            if moved:
                self.body_pose.update(moved)
                self._put_poses(moved)
            for s_ in SIDES_:
                sph = saved["sph"].get(s_)
                if sph is not None or self._held_sph.get(s_) is not None:
                    self._set_held_spheres(self.arms[s_], sph)
                    self._held_sph[s_] = sph
            self.cull_at = None

    def _set_held_spheres(self, arm, sph):
        """Write the held link's spheres (None: emptied) into every robot model of the arm."""
        t = arm.torch
        link = held_link(arm.side)
        for kc in arm.kcs:
            if sph is None:
                kc.detach_object(link)
            else:
                kc.attach_object(sphere_tensor=t.as_tensor(sph, device=kc.link_spheres.device,
                                                           dtype=kc.link_spheres.dtype), link_name=link)

    def _box_of(self, name):
        """The object's box (every collider) in the frame of its first collider, cached."""
        if name not in self._held_box:
            cols = self.by_owner[f"object:{name}"]
            frame = cols[0]
            inv = np.linalg.inv(G.world_pose(frame, self.body_pose.get))
            P = []
            for c in cols:
                if c.kind == "cuboid":
                    v = 0.5 * np.asarray(c.dims, float) * np.array(np.meshgrid([-1, 1], [-1, 1], [-1, 1])).reshape(3, -1).T
                else:
                    v = np.asarray(c.vertices, float)
                M = inv @ G.world_pose(c, self.body_pose.get)
                P.append(v @ M[:3, :3].T + M[:3, 3])
            P = np.vstack(P)
            self._held_box[name] = (frame, P.min(0), P.max(0))
        return self._held_box[name]

    @contextmanager
    def part_at(self, name, q):
        """Colliders of articulated part ``name`` at joint value q for the queries inside (checking
        a motion that moves the part, e.g. riding a door shut); back to the synced poses after."""
        from curobo.types.math import Pose
        a = self.ann.art(name)
        cols = self.by_owner.get(f"part:{a['name']}", [])
        q0 = self.part_q0.get(a["name"], q)
        M = self.ann.motion(a, q) @ np.linalg.inv(self.ann.motion(a, q0))
        saved = {c.body: self.body_pose.get(c.body) for c in cols}

        def place(poses):
            for b, T in poses.items():
                if T is None:
                    self.body_pose.pop(b, None)
                else:
                    self.body_pose[b] = T
            for c in self.cols.items:
                if c.body in poses:
                    self.checker.update_obstacle_pose(c.name, Pose.from_list(G.pose7(G.world_pose(c, self.body_pose.get))))
        place({b: M @ self.body0[b] for b in saved})
        try:
            yield
        finally:
            place(saved)

    @staticmethod
    def box_corners(c):
        """The 8 corners of collider ``c``'s box in its own frame (G.world_pose places them)."""
        signs = np.array(np.meshgrid([-1, 1], [-1, 1], [-1, 1])).reshape(3, -1).T
        if c.kind == "cuboid":
            return 0.5 * np.asarray(c.dims, float) * signs
        lo, hi = c.vertices.min(0), c.vertices.max(0)
        return (lo + hi) / 2 + (hi - lo) / 2 * signs

    def _owner_box(self, owner):
        """World AABB of ``owner``'s colliders at their synced poses: their corners, not their
        bounding spheres (a flat tray's sphere box is 0.34 m tall, and a TCP target above it
        made the tray a target: no obstacle to place_above, T12)."""
        P = []
        for c in self.by_owner.get(owner, []):
            T = G.world_pose(c, self.body_pose.get)
            P.append(self._corners[c.name] @ T[:3, :3].T + T[:3, 3])
        P = np.vstack(P) if P else np.zeros((2, 3))
        return P.min(0), P.max(0)

    @staticmethod
    def _inside(a, b, pad=0.0):
        ca = (a[0] + a[1]) / 2
        return bool(np.all(ca > b[0] - pad) and np.all(ca < b[1] + pad))

    def take_relaxed(self, side):
        """What ``side``'s collision queries left out since the last call (the motion record's
        ``relaxed``, Clearance.motion), and start over."""
        return self.relaxed.pop(side, set())

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
        arm.prepare(kin, other_q, links, self.live_locks())
        if collision:
            # with a load the hand goes where the load goes, not to touch what is there: a tray it
            # is put into stays an obstacle (T12); nor on the free part of an approach (coll_kw
            # exempt_targets False): only its contact segment touches the target (T20 knocked
            # the bottle it was reaching for)
            allow = set() if self.held.get(kin.side) or not coll_kw.get("exempt_targets", True) else \
                self._targets_allow([np.asarray(p, float) for p in targets])
            # objects the fingers may touch (Motion.query, Spec.touch): no obstacle here; the rest of
            # the arm is checked against them apart (path_free_only)
            allow = allow | getattr(self, "finger_touch", set())
            self.exempt = sorted(o.split(":", 1)[1] for o in allow)
            rel = self.relaxed.setdefault(kin.side, set())
            if own:
                rel.add("hand" if own is HAND_LINKS else "fingers")
            if self.exempt:
                rel.add("exempt")
            self._apply(kin.base_p[:2], allow=allow, side=kin.side)
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

    def ik_set(self, kin, P, Rs, q0, collision, other_q=None, coll_kw=None, weights=None):
        """Per TCP pose (P[i], Rs[i]) of a goal set: a solution near q0 (``weights``: per joint, on
        the distance; and clear of the joint limits), collision-free with ``collision``, else None
        -- all of them at once: one batched
        kinematic IK, one feasibility check of every solution, one batched world-aware IK for the
        poses whose kinematic solutions all collide."""
        STATS["ik"] += 1
        q0 = np.asarray(q0, float)
        w = np.ones(len(q0)) if weights is None else np.asarray(weights, float)
        with self._query(kin, other_q, coll_kw, list(P), collision) as arm:
            Q, ok = arm.ik_batch(P, Rs, q0, False)
            if collision and ok.any():
                free = ok.copy()
                free[ok] = arm.feasible(Q[ok])
                blocked = [i for i in range(len(P)) if ok[i].any() and not free[i].any()]
                if blocked:
                    Qc, okc = arm.ik_batch(np.asarray(P)[blocked], [Rs[i] for i in blocked], q0, True)
                    Q[blocked], free[blocked] = Qc, okc
                ok = free
            out = []
            for Qi, oki in zip(Q, ok):
                if not oki.any():
                    out.append(None)
                    continue
                cand = Qi[oki]
                margin = np.min(np.minimum(cand - arm.lo, arm.hi - cand)[:, 2:], axis=1)
                score = np.max(np.abs(cand - q0) * w, axis=1) + 10.0 * np.maximum(0.0, LIMIT_CLEAR - margin)
                out.append(cand[int(np.argmin(score))])
        STATS["ik_ok"] += sum(q is not None for q in out)
        return out

    @_timed("cart_s")
    def cart_path(self, kin, q0, p_goal, R_goal, step, collision, other_q=None, coll_kw=None):
        """Straight TCP line (slerp orientation) as cuRobo IK solutions (batched, see
        _Arm.path_ik); continuous (<= MAX_STEP rad per joint between waypoints) and, with
        collision, every waypoint and the joint segments between them feasible."""
        STATS["cart"] += 1
        q0 = np.asarray(q0, float)
        p0, R0 = kin.tcp(q0)
        with self._query(kin, other_q, coll_kw, [p0, p_goal], collision) as arm:
            out, ok = self._line(arm, q0, p0, R0, p_goal, R_goal, step, collision)
            if not ok and step < COARSE_STEP:
                # one failed IK of many waypoints sinks a fine line that a coarser one passes
                out, ok = self._line(arm, q0, p0, R0, p_goal, R_goal, COARSE_STEP, collision)
                if ok:                                      # densified for smooth tracking
                    dense, prev = [], q0
                    for q in out:
                        k = max(1, int(np.max(np.abs(q - prev)) / 0.01))
                        dense += [prev + (q - prev) * u for u in np.linspace(0, 1, k + 1)[1:]]
                        prev = q
                    out = dense
        STATS["cart_ok"] += int(ok)
        return out, ok

    def _line(self, arm, q0, p0, R0, p_goal, R_goal, step, collision):
        """cart_path's waypoints at ``step`` m (and 0.05 rad of orientation) apart."""
        from scipy.spatial.transform import Slerp
        n = max(2, int(np.ceil(np.linalg.norm(p_goal - p0) / step)) + 1)
        ang = np.linalg.norm(Rotation.from_matrix(R_goal @ R0.T).as_rotvec())
        n = max(n, int(np.ceil(ang / 0.05)) + 1)
        slerp = Slerp([0, 1], Rotation.from_matrix([R0, R_goal]))
        us = np.linspace(0, 1, n)[1:]
        out, ok = arm.path_ik([p0 + (p_goal - p0) * u for u in us], [slerp(u).as_matrix() for u in us], q0)
        if ok and collision and not self._segments_free(arm, [q0] + out):
            ok = False
        return out, ok

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

    @_timed("check_s")
    def path_free(self, kin, qs, other_q=None, coll_kw=None):
        STATS["check"] += 1
        with self._query(kin, other_q, coll_kw) as arm:
            return self._segments_free(arm, [np.asarray(q, float) for q in qs])

    def touch_owner(self, name):
        """The collider owner of a Spec.touch name: the object, else the articulated part of that name."""
        if self.by_owner.get(f"object:{name}") or name in self.ann.objects:
            return f"object:{name}"
        if any(a["name"] == name for a in self.ann.articulated):
            return f"part:{name}"
        raise KeyError(f"touch {name}: neither an object nor an articulated part")

    @_timed("check_s")
    def path_free_only(self, kin, qs, names, other_q=None, coll_kw=None):
        """The arm without the touching links clear of what they may touch alone, all along ``qs``
        (Spec.touch: the fingers -- or the whole hand, (name, "hand") -- may touch it, the rest of
        the arm may not).  ``names``: object / part names (the fingers'), or (name, links) pairs."""
        STATS["check"] += 1
        by_links = {}
        for n, links in touch_entries(names):
            by_links.setdefault(links, set()).add(self.touch_owner(n))
        touch, self.finger_touch = getattr(self, "finger_touch", set()), set()
        try:
            for links, owners in sorted(by_links.items()):
                kw = {**(coll_kw or {}), "ignore_fingers": True}
                if links == "hand":
                    kw["hand_touches_part"] = True          # _query: the hand links off (HAND_LINKS)
                with self._query(kin, other_q, kw) as arm:
                    on = [c for c in self.cols.items if self.enabled[c.name]]
                    try:
                        for c in on:
                            self._set_enabled(c, False)
                        for c in self.cols.items:
                            if c.owner in owners:
                                self._set_enabled(c, True)
                        if not self._segments_free(arm, [np.asarray(q, float) for q in qs]):
                            return False
                    finally:
                        for c in self.cols.items:
                            if c.owner in owners:
                                self._set_enabled(c, False)
                        for c in on:
                            self._set_enabled(c, True)
            return True
        finally:
            self.finger_touch = touch
            self.cull_at = None

    @_timed("plan_s")
    def plan(self, kin, q0, q1, other_q=None, coll_kw=None, carry=False):
        """cuRobo joint-space trajectory q0 -> q1 (waypoints after q0) or (None, status).
        ``carry`` (an object in the hand): the held object may not tilt more than CARRY_TILT
        on the way; a trajectory that would is re-planned to q1's TCP pose with the tilt held
        (it then ends at that pose, not necessarily at q1)."""
        STATS["plan"] += 1
        q0, q1 = np.asarray(q0, float), np.asarray(q1, float)
        with self._query(kin, other_q, coll_kw) as arm:
            qs, status = self._plan_js(arm, kin, q0, q1, carry)
        STATS["plan_ok"] += int(qs is not None)
        return qs, status

    def _plan_js(self, arm, kin, q0, q1, carry):
        """plan's trajectory in the current query state."""
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
        return qs, status

    @_timed("plan_s")
    def plan_to(self, kin, q0, p0, p, R, other_q=None, coll_kw=None, carry=False, q_goal=None):
        """The planned trajectory of a Cartesian leg p0 -> (p, R) whose straight line is blocked.
        First constrained to the pose: with an object in the hand the tilt is held throughout;
        otherwise the trajectory may leave the line to clear the obstacle but ends with a
        straight approach along it (Arm.approach_metric).  Else to the joint goal ``q_goal`` (a
        solution of (p, R), e.g. the one find_park validated): the straight joint move when it is
        free and keeps a held object level, else a trajectory, the tilt held with a load.
        (qs, "pose" | "joint") or (None, status)."""
        STATS["plan_to"] = STATS.get("plan_to", 0) + 1
        q0 = np.asarray(q0, float)
        with self._query(kin, other_q, coll_kw, [p0, p]) as arm:
            R0 = kin.tcp(q0)[1]
            if carry and tilt(R0, R) <= CARRY_TILT:
                metric = arm.tilt_metric()
            else:
                metric = arm.approach_metric(p0, p, R)
            qs, status = None, "leg follows no TCP axis: no constrained approach"
            if metric is not None:
                qs, status = arm.plan_pose(q0, np.asarray(p, float), R, metric)
                if qs is not None and carry and max_tilt(kin, R0, qs) > CARRY_TILT + tilt(R0, R):
                    qs, status = None, "held object tilts on the planned leg"
            how = "pose"
            if qs is None and q_goal is not None:
                q_goal = np.asarray(q_goal, float)
                how = "joint"
                if self._segments_free(arm, [q0, q_goal]) and not (carry and tips_over(kin, q0, q_goal)):
                    qs = [q_goal]
                else:
                    qs, s2 = self._plan_js(arm, kin, q0, q_goal, carry)
                    status = f"{status}; joint goal: {s2}"
        STATS["plan_to_ok"] = STATS.get("plan_to_ok", 0) + int(qs is not None)
        return (qs, how) if qs is not None else (None, status)

    def _sphere_depths(self, arm, q, gap=0.0):
        """(spheres (n, 4) world, penetration depth (n,), link of each) of the arm's robot model at q;
        depth 0 for spheres clear of the world or switched off.  ``gap`` > 0: each sphere grown by
        it (cuRobo's activation distance), so > 0 means within ``gap`` of the world."""
        import torch
        from curobo.geom.sdf.world import CollisionQueryBuffer
        sph = arm.spheres(np.asarray(q, float))
        kc = arm.kcs[0]
        idx = kc.link_sphere_idx_map.cpu().numpy()
        by_idx = {v: k for k, v in kc.link_name_to_idx_map.items()}
        q4 = sph.view(1, 1, -1, 4).contiguous()
        buf = CollisionQueryBuffer.initialize_from_shape(q4.shape, arm.mg.tensor_args, self.checker.collision_types)
        d = self.checker.get_sphere_distance(q4, buf, torch.ones(1, device="cuda"),
                                             torch.full((1,), float(gap), device="cuda"),
                                             sum_collisions=False).view(-1).cpu().numpy()
        s = sph.cpu().numpy()
        d = np.where(s[:, 3] > 0, np.maximum(d, 0.0), 0.0)
        return s, d, [by_idx.get(int(i), str(i)) for i in idx]

    def near(self, kin, q, gap, other_q=None, coll_kw=None):
        """Whether the arm's robot model at q (with what the hand carries, inside ``scope``) comes
        within ``gap`` m of the world.  A held box rests on its support at depth 0: its spheres are
        inscribed in the box, so a contact is told by a gap, not by penetration."""
        with self._query(kin, other_q, coll_kw) as arm:
            return bool(self._touching(arm, np.clip(np.asarray(q, float), arm.lo, arm.hi), gap))

    def _touching(self, arm, q, gap=0.0):
        """{link: depth} of the robot's links penetrating the world at q (grown by ``gap``)."""
        _, d, links = self._sphere_depths(arm, q, gap)
        hits = {}
        for i in np.nonzero(d > 0)[0]:
            hits[links[i]] = max(hits.get(links[i], 0.0), float(d[i]))
        return hits

    def contacts_by_owner(self, kin, q, other_q=None, reach=0.5):
        """{owner: {link: depth m}}: what each obstacle within ``reach`` of the TCP is penetrated by
        at q, every link of the arm checked (fingers too) and no target exempt -- the full model,
        not the one a motion ran under.  One query per owner with only its colliders on; for
        measuring (what the open hand at a grasp pose touches: grasp_contacts), not for planning."""
        with self._query(kin, other_q, {"exempt_targets": False}) as arm:
            q = np.clip(np.asarray(q, float), arm.lo, arm.hi)
            if not self._touching(arm, q):
                return {}
            tcp = kin.tcp(q)[0]
            on = [c for c in self.cols.items if self.enabled[c.name]]
            owners = {}
            for c in on:
                if np.linalg.norm(self._centre(c) - tcp) - self._extent[c.name][1] < reach:
                    owners.setdefault(c.owner, []).append(c)
            out = {}
            try:
                for c in on:
                    self._set_enabled(c, False)
                for owner, cs in owners.items():
                    for c in cs:
                        self._set_enabled(c, True)
                    hits = self._touching(arm, q)
                    if hits:
                        out[owner] = {l: round(v, 4) for l, v in sorted(hits.items(), key=lambda t: -t[1])}
                    for c in cs:
                        self._set_enabled(c, False)
            finally:
                for c in on:
                    self._set_enabled(c, True)
            return out

    def explain(self, kin, q, other_q=None, coll_kw=None):
        """Which links of q penetrate the world (deepest first), else self collision / limits."""
        with self._query(kin, other_q, coll_kw) as arm:
            return self._explain(arm, np.clip(np.asarray(q, float), arm.lo, arm.hi))

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

    # ------------------------------------------------------------- whole-body base check
    def body_spheres(self, rig, postures):
        """(P, S, 4) spheres of the robot above its base in the frame of its current base, one set per
        posture (q_right: torso, waist, 7 right-arm joints; q_left: 7 left-arm joints): every link of
        both arms, torso and head at that posture, and what each hand holds as box_spheres riding
        rigidly on its TCP (where it sits in the hand now).  The base column has no spheres (its
        collider is off): its footprint is checked on the annotated boxes (WorldModel)."""
        import torch
        model, names, link_of, _ = self._monitor_model()
        self._mon_set(rig)
        rows = []
        for qr, ql in postures:
            vals = {"base_x": 0.0, "base_y": 0.0, "base_yaw": 0.0}
            vals.update(zip(rig.kin.names, np.asarray(qr, float)))
            vals.update(zip(rig.left_kin.names[2:], np.asarray(ql, float)[-7:]))
            rows.append([float(vals.get(n, 0.0)) for n in names])
        q = torch.tensor(rows, device="cuda", dtype=torch.float32)
        sph = model.get_state(q).link_spheres_tensor.view(len(postures), -1, 4).cpu().numpy().astype(float)
        on = sph[0, :, 3] > 0
        sph = sph[:, on]
        self.body_names = [l for l, k in zip(link_of, on) if k]
        bx, by, byaw = rig.base_pose()
        T_base = np.eye(4)
        T_base[:2, :2] = [[math.cos(math.radians(byaw)), -math.sin(math.radians(byaw))],
                          [math.sin(math.radians(byaw)), math.cos(math.radians(byaw))]]
        T_base[:2, 3] = bx, by
        inv_base = np.linalg.inv(T_base)
        extra = []
        for side, kin, h in (("right", rig.kin, rig.held), ("left", rig.left_kin, getattr(rig, "left_held", None))):
            if h is None or h.get("name") not in self.ann.objects or not self.by_owner.get(f"object:{h['name']}"):
                continue
            if h.get("kind") == "bimanual" and side == "left":
                continue
            frame, lo, hi = self._box_of(h["name"])
            b = box_spheres(lo, hi)
            T_obj = G.world_pose(frame, self.body_pose.get)
            pts = (inv_base[:3, :3] @ (b[:, :3] @ T_obj[:3, :3].T + T_obj[:3, 3]).T).T + inv_base[:3, 3]
            # the TCP in the base frame, wherever kin's base sits (find_park moves it around)
            T_kin = np.eye(4)
            T_kin[:3, :3], T_kin[:3, 3] = kin.base_R, kin.base_p
            inv_kin = np.linalg.inv(T_kin)
            now = rig.q_cmd if side == "right" else np.r_[rig.q_cmd[:2], rig.left_q_cmd]
            T_now = inv_kin @ self._tcp_T(kin, now)
            local = (pts - T_now[:3, 3]) @ T_now[:3, :3]              # in the TCP frame
            sets = []
            for qr, ql in postures:
                T = inv_kin @ self._tcp_T(kin, qr if side == "right" else np.r_[np.asarray(qr, float)[:2], ql[-7:]])
                sets.append(np.c_[local @ T[:3, :3].T + T[:3, 3], b[:, 3]])
            extra.append(sets)
            self.body_names += [f"held:{h['name']}"] * len(b)
        return np.concatenate([sph] + [np.stack(e) for e in extra], axis=1)

    @staticmethod
    def _tcp_T(kin, q):
        p, R = kin.tcp(np.asarray(q, float))
        T = np.eye(4)
        T[:3, :3], T[:3, 3] = R, p
        return T

    @_timed("base_s")
    def base_depths(self, rig, poses, spheres, chunk=BASE_CHUNK):
        """(P, N) deepest penetration (m, >= 0) of the robot into the world with its base at each of
        ``poses`` ((N, 3): x, y, yaw rad) and its body as each of ``spheres`` ((P, S, 4) from
        body_spheres).  The world: every collider within reach of the poses that neither hand holds,
        objects and parts at their synced poses.  The planner's world (enabled colliders, cull centre)
        is exactly as before when this returns."""
        import torch
        from curobo.geom.sdf.world import CollisionQueryBuffer
        poses = np.atleast_2d(np.asarray(poses, float))
        spheres = np.asarray(spheres, float)
        P, S = spheres.shape[:2]
        out = np.zeros((P, len(poses)))
        if not len(poses):
            return out
        reach = float(np.max(np.linalg.norm(spheres[..., :2], axis=-1) + spheres[..., 3]))
        lo, hi = poses[:, :2].min(0) - reach - 0.1, poses[:, :2].max(0) + reach + 0.1
        scope = getattr(self, "_base_scope", None)
        if scope is not None and np.all(lo >= scope[0]) and np.all(hi <= scope[1]):
            flip, use = [], set()                     # base_world already set the world for the region
        else:
            use = self._region_colliders(lo, hi)
            flip = [c for c in self.cols.items if self.enabled[c.name] != (c.name in use)]
        sph = torch.as_tensor(spheres, device="cuda", dtype=torch.float32)          # (P, S, 4)
        try:
            for c in flip:
                self._set_enabled(c, c.name in use)
            for k in range(0, len(poses), chunk):
                pc = torch.as_tensor(poses[k:k + chunk], device="cuda", dtype=torch.float32)
                n = len(pc)
                cy, sy = torch.cos(pc[:, 2]), torch.sin(pc[:, 2])
                x, y = sph[..., 0][:, None], sph[..., 1][:, None]                     # (P, 1, S)
                w = torch.empty((P, n, S, 4), device="cuda", dtype=torch.float32)
                w[..., 0] = cy[None, :, None] * x - sy[None, :, None] * y + pc[None, :, 0, None]
                w[..., 1] = sy[None, :, None] * x + cy[None, :, None] * y + pc[None, :, 1, None]
                w[..., 2] = sph[..., 2][:, None]
                w[..., 3] = sph[..., 3][:, None]
                q4 = w.view(P * n, 1, S, 4).contiguous()
                buf = CollisionQueryBuffer.initialize_from_shape(q4.shape, self.arms["right"].mg.tensor_args,
                                                                 self.checker.collision_types)
                d = self.checker.get_sphere_distance(q4, buf, torch.ones(1, device="cuda"),
                                                     torch.zeros(1, device="cuda"), sum_collisions=False)
                out[:, k:k + n] = d.view(P, n, S).max(dim=2).values.clamp(min=0.0).cpu().numpy()
        finally:
            for c in flip:
                self._set_enabled(c, c.name not in use)
            if flip:
                self.cull_at = None
        return out

    def static_top(self, lo, hi, below):
        """The highest top (m) of the static colliders whose box overlaps the xy box [lo, hi] and
        tops out below ``below``: the surface something there rests on when no annotated support
        says so (a floor, a rug: T12's rug collider tops out 3.6 mm above the toy car's box
        bottom), or None.  The static colliders' boxes are computed once (they do not move)."""
        if getattr(self, "_static_boxes", None) is None:
            boxes = []
            for c in self.cols.items:
                if c.owner == "static":
                    T = G.world_pose(c, self.body_pose.get)
                    P = self._corners[c.name] @ T[:3, :3].T + T[:3, 3]
                    boxes.append(np.r_[P.min(0), P.max(0)])
            self._static_boxes = np.array(boxes).reshape(-1, 6)
        B = self._static_boxes
        m = (B[:, 0] < hi[0]) & (B[:, 3] > lo[0]) & (B[:, 1] < hi[1]) & (B[:, 4] > lo[1]) & (B[:, 5] < below)
        return float(B[m, 5].max()) if m.any() else None

    def _region_colliders(self, lo, hi):
        """Names of the colliders whose box reaches the xy box [lo, hi] that neither hand holds."""
        held = set(self.held["right"]) | set(self.held["left"])
        key = tuple(sorted(held))
        if getattr(self, "_centres_key", None) != (id(self.body_pose), self._sync_n, key):
            self._centres_key = (id(self.body_pose), self._sync_n, key)
            self._centres = np.array([self._centre(c)[:2] for c in self.cols.items])
            self._radii = np.array([self._extent[c.name][1] for c in self.cols.items])
            self._usable = np.array([c.owner not in held for c in self.cols.items])
        m = self._usable & np.all(self._centres + self._radii[:, None] > lo, axis=1) & \
            np.all(self._centres - self._radii[:, None] < hi, axis=1)
        return {c.name for c, k in zip(self.cols.items, m) if k}

    @contextmanager
    def base_world(self, lo, hi):
        """The world of base_depths for every query inside whose poses stay in the xy box [lo, hi]
        (the reach of the robot added): set once, restored after (a base plan's many queries)."""
        r = 1.5
        lo, hi = np.asarray(lo, float) - r, np.asarray(hi, float) + r
        use = self._region_colliders(lo, hi)
        flip = [c for c in self.cols.items if self.enabled[c.name] != (c.name in use)]
        try:
            for c in flip:
                self._set_enabled(c, c.name in use)
            self._base_scope = (lo, hi)               # the colliders enabled: base_depths' region must fit
            yield
        finally:
            self._base_scope = None
            for c in flip:
                self._set_enabled(c, c.name not in use)
            self.cull_at = None

    def base_explain(self, rig, pose, spheres, top=4):
        """What the robot runs into with its base at ``pose`` (x, y, yaw rad) and its body as
        ``spheres`` ((S, 4), the last body_spheres set): its deepest (part, entity, mm)."""
        import torch
        from curobo.geom.sdf.world import CollisionQueryBuffer
        x, y, yaw = pose
        c, s_ = math.cos(yaw), math.sin(yaw)
        w = np.asarray(spheres, float).copy()
        w[:, 0], w[:, 1] = c * spheres[:, 0] - s_ * spheres[:, 1] + x, s_ * spheres[:, 0] + c * spheres[:, 1] + y
        held = set(self.held["right"]) | set(self.held["left"])
        use = {c_.name for c_ in self.cols.items if c_.owner not in held and
               np.hypot(*(self._centre(c_)[:2] - [x, y])) - self._extent[c_.name][1] < 1.5}
        cols = [c_ for c_ in self.cols.items if c_.name in use]
        flip = [c_ for c_ in self.cols.items if self.enabled[c_.name] != (c_.name in use)]
        try:
            for c_ in flip:
                self._set_enabled(c_, c_.name in use)
            q4 = torch.as_tensor(w, device="cuda", dtype=torch.float32).view(1, 1, -1, 4).contiguous()
            buf = CollisionQueryBuffer.initialize_from_shape(q4.shape, self.arms["right"].mg.tensor_args,
                                                             self.checker.collision_types)
            d = self.checker.get_sphere_distance(q4, buf, torch.ones(1, device="cuda"), torch.zeros(1, device="cuda"),
                                                 sum_collisions=False).view(-1).cpu().numpy()
        finally:
            for c_ in flip:
                self._set_enabled(c_, c_.name not in use)
            self.cull_at = None
        out, seen = [], set()
        for i in np.argsort(-d):
            if d[i] <= 0 or len(out) >= top:
                break
            name = self.body_names[i] if i < len(self.body_names) else "?"
            ent = self._nearest_entity(w[i, :3], float(w[i, 3]), {}, cols)
            if (name, ent) not in seen:
                seen.add((name, ent))
                out.append((name, ent, round(float(d[i]) * 1000)))
        return out

    # ------------------------------------------------------------- contact monitor
    def _monitor_model(self):
        """Whole-robot kinematics (base, both arms) for the contact monitor and the base check,
        apart from the arm solvers so their locks are never touched; the head and finger joints
        are locked in the robot config, set to the robot's values before each use (_mon_set)."""
        if getattr(self, "_mon", None) is None:
            import yaml
            from curobo.cuda_robot_model.cuda_robot_model import CudaRobotModel
            from curobo.types.base import TensorDeviceType
            from curobo.types.robot import RobotConfig
            cfg = yaml.safe_load(open(ROBOT_CFG))["robot_cfg"]
            k = cfg["kinematics"]
            k["urdf_path"] = str(ROOT / k["urdf_path"])
            k["asset_root_path"] = str(ROOT / k["asset_root_path"])
            model = CudaRobotModel(RobotConfig.from_dict(cfg, TensorDeviceType()).kinematics)
            kc = model.kinematics_config
            by_idx = {v: k for k, v in kc.link_name_to_idx_map.items()}
            links = [by_idx.get(int(i), str(i)) for i in kc.link_sphere_idx_map.cpu().numpy()]
            self._mon = (model, list(model.joint_names), links, _Locks([model], k["lock_joints"], k["urdf_path"]))
        return self._mon

    def _mon_set(self, rig):
        """The monitor model's head and both fingers of each hand where the robot has them (they
        are locked joints there: values for them in a joint row were dropped, the fingers stood
        fully open and the head straight ahead)."""
        vals = dict(rig.head_q())
        for side, f in (("right", rig.fingers()), ("left", rig.left_fingers())):
            vals[f"{side}_gripper_left_finger_axis"], vals[f"{side}_gripper_right_finger_axis"] = map(float, f[:2])
        self._monitor_model()[3].set(vals)

    def _entity(self, c):
        """The name a contact with collider ``c`` is reported under: the object or part, else the
        annotated furniture its prim path runs through, else the path's last two parts."""
        if c.owner != "static":
            return c.owner.split(":", 1)[1]
        cache = self.__dict__.setdefault("_entity_of", {})
        if c.name not in cache:
            parts = c.name.strip("/").split("/")
            known = {o["name"] for o in self.ann.obstacles}
            cache[c.name] = next((p for p in reversed(parts) if p in known), "/".join(parts[-2:]))
        return cache[c.name]

    def entity_of_path(self, path):
        """The entity (as _entity names it) of the collider at prim ``path``, for a PhysX contact
        report; a path the planner's world lacks: the annotated object, part or furniture its path
        runs through, else its last two parts."""
        by_name = self.__dict__.get("_col_by_name")
        if by_name is None:
            by_name = self._col_by_name = {c.name: c for c in self.cols.items}
        c = by_name.get(path)
        if c is not None:
            return self._entity(c)
        cache = self.__dict__.setdefault("_entity_of", {})
        if path not in cache:
            parts = path.strip("/").split("/")
            prims = {o["prim"].strip("/"): n for n, o in self.ann.objects.items() if o.get("prim")}
            known = {o["name"] for o in self.ann.obstacles}
            name = next((prims[p] for p in ("/".join(parts[:i]) for i in range(len(parts), 0, -1)) if p in prims),
                        None)
            cache[path] = name or next((p for p in reversed(parts) if p in known), "/".join(parts[-2:]))
        return cache[path]

    def _nearest_entity(self, p, r, poses, cols):
        """Entity of the collider in ``cols`` closest to sphere (p, r): distance to its box in its own frame."""
        c = self._nearest_collider(p, r, poses, cols)
        if c is None:
            return "?"
        return self._entity(c) if c.owner != "static" else self._furniture_at(p, r) or self._entity(c)

    def _nearest_collider(self, p, r, poses, cols):
        """The collider in ``cols`` closest to sphere (p, r) (distance to its box in its own frame), or None."""
        at = lambda b: poses[b] if b in poses else self.body_pose.get(b)
        best, out = np.inf, None
        for c in cols:
            ctr, rad = self._extent[c.name]
            T = G.world_pose(c, at)
            if np.linalg.norm(T[:3, :3] @ ctr + T[:3, 3] - p) > rad + r + 0.02:
                continue
            local = T[:3, :3].T @ (p - T[:3, 3])
            if c.kind == "cuboid":
                lo, hi = -0.5 * np.asarray(c.dims, float), 0.5 * np.asarray(c.dims, float)
            else:
                lo, hi = c.vertices.min(0), c.vertices.max(0)
            d = float(np.linalg.norm(np.maximum(np.maximum(lo - local, local - hi), 0.0)))
            if d < best:
                best, out = d, c
        return out

    def _furniture_at(self, p, r):
        """The annotated obstacle a static contact at sphere (p, r) belongs to: the smallest box
        holding it, else the nearest within 25 cm, else None (a static collider's prim path
        often names only a mesh)."""
        best, name = (np.inf, np.inf), None
        for o in self.ann.obstacles:
            lo, hi = np.asarray(o["aabb"][:3], float), np.asarray(o["aabb"][3:], float)
            gap = float(np.linalg.norm(np.maximum(np.maximum(lo - p, p - hi), 0.0))) - r
            rank = (max(gap, 0.0), float(np.prod(np.maximum(hi - lo, 1e-3))))
            if gap < 0.25 and rank < best:
                best, name = rank, o["name"]
        return name

    @_timed("monitor_s")
    def robot_contacts(self, rig, min_depth=0.0):
        """[(link, entity, depth m)] of robot links inside the world at the real joint state and
        base pose: objects and parts at their simulator poses, nothing either hand holds (nor
        what it carries), obstacles within CULL.  What a hand holds counts as part of the robot:
        its box (box_spheres) at its simulator pose, reported as link ``held:<name>``.  The
        planner's world (obstacle poses, enabled colliders, cull centre) is exactly as before
        when this returns."""
        import torch
        from curobo.geom.sdf.world import CollisionQueryBuffer
        model, names, links, _ = self._monitor_model()
        self._mon_set(rig)
        bx, by, byaw = rig.base_pose()
        vals = {"base_x": bx, "base_y": by, "base_yaw": math.radians(byaw)}
        vals.update(zip(rig.kin.names, rig.q()))
        vals.update(zip(rig.left_kin.names[2:], rig.left_q()[2:]))
        q = torch.tensor([[float(vals.get(n, 0.0)) for n in names]], device="cuda", dtype=torch.float32)
        sph = model.get_state(q).link_spheres_tensor.view(1, 1, -1, 4).contiguous()
        carried = sorted({h["name"] for h in (rig.held, getattr(rig, "left_held", None))
                          if h and self.by_owner.get(f"object:{h['name']}")})
        held = set(self.held["right"]) | set(self.held["left"]) | {f"object:{n}" for n in carried}
        # colliders the check uses: within CULL of the base, not held; and the objects and parts
        # within MONITOR_NEAR, whose simulator poses are read (reading them all was 24 ms a check).
        # Kept while the base stays within RECULL and the hands hold the same things.
        key = (round(bx / RECULL), round(by / RECULL), frozenset(held))
        if getattr(self, "_mon_key", None) != key:
            base = np.array([bx, by])
            self._mon_key = key
            self._mon_cols, self._mon_near = [], set()
            for c in self.cols.items:
                gap = np.hypot(*(self._centre(c)[:2] - base)) - self._extent[c.name][1]
                if c.owner not in held and gap < CULL:
                    self._mon_cols.append(c)
                    if c.owner != "static" and gap < MONITOR_NEAR:
                        self._mon_near.add(c.owner)
        poses = self._live_poses(rig, record=False, owners=self._mon_near | {f"object:{n}" for n in carried})
        if carried:
            live = lambda b: poses[b] if b in poses else self.body_pose.get(b)
            extra = []
            for n in carried:
                frame, lo, hi = self._box_of(n)
                T = G.world_pose(frame, live)
                bs = box_spheres(lo, hi)
                extra.append(np.c_[bs[:, :3] @ T[:3, :3].T + T[:3, 3], bs[:, 3]])
                links = links + [f"held:{n}"] * len(bs)
            sph = torch.cat([sph, torch.as_tensor(np.vstack(extra), device=sph.device,
                                                  dtype=sph.dtype).view(1, 1, -1, 4)], dim=2).contiguous()
        use = {c.name for c in self._mon_cols}
        flip = [c for c in self.cols.items if self.enabled[c.name] != (c.name in use)]
        try:
            self._put_poses(poses)
            for c in flip:
                self._set_enabled(c, c.name in use)
            buf = CollisionQueryBuffer.initialize_from_shape(sph.shape, self.arms["right"].mg.tensor_args,
                                                             self.checker.collision_types)
            d = self.checker.get_sphere_distance(sph, buf, torch.ones(1, device="cuda"),
                                                 torch.zeros(1, device="cuda"), sum_collisions=False)
            d = d.view(-1).cpu().numpy()
            s = sph.view(-1, 4).cpu().numpy()
            out = {}
            for i in np.nonzero((d > min_depth) & (s[:, 3] > 0))[0]:
                pair = (links[i], self._nearest_entity(s[i, :3], float(s[i, 3]), poses, self._mon_cols))
                out[pair] = max(out.get(pair, 0.0), float(d[i]))
        finally:
            for c in flip:
                self._set_enabled(c, c.name not in use)
            self._put_poses({b: self.body_pose.get(b) for b in poses})
        return [(l, e, v) for (l, e), v in sorted(out.items())]
