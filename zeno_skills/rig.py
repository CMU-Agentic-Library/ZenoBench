"""Isaac Sim runtime for Zeno Malo: joint-drive control, holonomic base,
state readout and recording.  Only robot drive targets (the base's x, y and yaw joints
among them) are ever written; objects and furniture move only through contact.
"""

from __future__ import annotations

import json
import math
from contextlib import contextmanager
from dataclasses import replace

import numpy as np

from .clearance import BASE_DRIVE, FREE, FREE_ELSE_STRAIGHT, HAND_LINKS, LEGACY, MONITOR_EVERY, Clearance
from .motion_state import Dropped, SkillFailure     # noqa: F401  (defined below the layers; re-exported here)
from .kinematics import ArmKin, FINGERS, LEFT_ARM_FOLD, tips_over, vel_limits, yaw_quat_wxyz
from .physics import ASSET, BASE_JOINTS, OBJECT_SLEEP, PHYSICS_HZ
from .primitives import HINT_REACH, HINT_TURN, LEAVE_GAP, LEAVE_MARGIN, LEAVE_MAX, ON_LINE, exit_length, near_pose  # noqa: F401
from .tolerances import HEAD_AT, RIDE_SLIP_LEADS, RIDE_STALL, SETTLE_STILL, SETTLE_TCP

BIG_SWING = 1.0           # rad: an unchecked joint move swinging further is planned (a 2 rad swing put the forearm through a trash can)
CARRY_VEL = 0.5           # rad/s: arm joint speed cap with an object in the hand (it must not be flung)
RIM_VEL = 0.25            # rad/s: ...with a container hanging from a one-hand rim pinch (it pivots in the pads)
# A follow ends when the arm has arrived or has stopped, not at a joint tolerance: 0.01 rad of one
# joint is 8 mm at the hand 0.8 m out, and the reach checks after it (TARGET_TOL, 5 mm)
# then took a hand still closing in for a blocked one (T06 s10 6.8 mm, T10 s11 7.9 mm, the mug of
# T14 shelf_taken s11 6 mm at its set-down, 11-06/11-07).
# SETTLE_TCP (arrived) and SETTLE_STILL (stopped): tolerances.py
SETTLE_WINDOW = 10        # physics ticks the stop is measured over (one turning point of a wobble is not a stop)
FREE_SPACE_KW = {"exempt_targets": False}   # coll_kw of free space: the fingers checked, no target exempted
FINGERS_KW = {}           # coll_kw of a park search's approach target: the fingers checked, the object at it exempted
                          # (where the approach's contact segment begins is the collision model's call at the time)


BASE_VMAX = np.array([1.0, 1.0, 2.0])     # m/s, m/s, rad/s: base velocity targets beyond are clipped
# Base drive speed caps (m/s, rad/s, the least ramp in s) by what the hands hold, kept in this one place:
# drive_base takes the cap of the load, a caller may only ask for slower.  Inherited (the navigate
# speeds from 32a2d66c, the one-hand cap from d705872b), never measured: docs/motion/COLLISION_PLAN.md §2.
DRIVE_EMPTY = (0.35, 0.8, 0.0)
DRIVE_LOADED = (0.25, 0.5, 0.0)      # an object in the right hand
DRIVE_SWINGING = (0.17, 0.30, 1.8)   # a container on a one-hand rim pinch, or a load in the left hand alone: it pivots
HELD_CHECK_EVERY = PHYSICS_HZ // 2      # ticks between check_held calls along a drive (inherited, unmeasured)
DRIVE_RAMP = 0.8                     # s: acceleration ramp of a drive that asks for none
RIDE_TICKS = 6000                    # physics ticks a ride (Rig.ride) runs at most (skills._ride's)
RIDE_LOG_EVERY = 60                  # ticks between ride events (and stall checks)
RIDE_STALL_CHECKS = 4                # checks in a row a part moved less than RIDE_STALL: stalled (skills._ride's;
                                     # RIDE_STALL, RIDE_SLIP_LEADS: tolerances.py)



# one arm of the rig by side: its planning chain (torso, waist, 7 arm joints), what it holds, its
# fingers (module functions: the old entries' tests bind Rig's methods to stand-ins)
def _chain_q(rig, side):
    return rig.q() if side == "right" else rig.left_q()


def _chain_cmd(rig, side):
    return rig.q_cmd.copy() if side == "right" else np.r_[rig.q_cmd[:2], rig.left_q_cmd]


def _set_chain_cmd(rig, side, q):
    """Command ``side``'s planning chain (the body with it: both arms ride on it)."""
    q = np.asarray(q, float)
    if side == "right":
        rig.q_cmd = q.copy()
    else:
        rig.q_cmd = np.r_[q[:2], rig.q_cmd[2:]]
        rig.left_q_cmd = q[2:].copy()


def _held_of(rig, side):
    return getattr(rig, "held" if side == "right" else "left_held", None)


def _fingers_of(rig, side):
    return rig.fingers() if side == "right" else rig.left_fingers()

SETTLE_OFF_LOG = 0.05   # rad: a follow that stops with a joint further off its command than this is logged (settle_off)
GRAVITY = 9.81          # m/s^2
PAYLOAD_REACH = 0.4     # m: a held load's centre of mass further than this from its hand's TCP is not in the hand
                        # (dropped, or the hold not cleared yet): no feedforward for it


def payload_torques(kin, q, com, mass):
    """The joint torques (one per joint of ``kin``'s chain) that carry ``mass`` kg at the world point
    ``com`` held rigidly in its hand at ``q``: J_com^T (0, 0, m g), J_com the position Jacobian of that
    point (the TCP's, its lever r = com - tcp added: v = v_tcp + w x r).  The robot's own links fly
    with gravity off (physics.fix_robot: the arm controller's gravity compensation); the load in the hand
    weighed on the position drives alone -- an edge-pinched book 9 mm low, a held notebook's carry
    sagging off its plan (liftdbg_1112, 11-12) -- so the controller compensates the payload too."""
    J, tcp, _ = kin.jac(np.asarray(q, float))
    r = np.asarray(com, float) - tcp
    skew = np.array([[0.0, -r[2], r[1]], [r[2], 0.0, -r[0]], [-r[1], r[0], 0.0]])
    Jp = J[:3] - skew @ J[3:]
    return Jp.T @ np.array([0.0, 0.0, mass * GRAVITY])


def _quat_R(q):
    w, x, y, z = (float(v) for v in q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


class Rig:
    sticky = None                # zeno_skills.sticky.StickyHands when the profile turns sticky hands on

    def __init__(self, sim, stage, robot, kin, world, ann, cams=None, stride=8, log=print,
                 first_person_camera=None, wrist_cameras=None):
        import torch
        from isaacsim.core.prims import SingleArticulation, SingleRigidPrim
        self.torch = torch
        self.sim, self.stage, self.robot, self.kin, self.world, self.ann = sim, stage, robot, kin, world, ann
        self.cams = cams or {}
        self.first_person_camera = first_person_camera
        self.wrist_cameras = wrist_cameras or {}
        self.arm = torch.tensor([robot.dof_names.index(n) for n in kin.names], dtype=torch.int32)
        self.fing = torch.tensor([robot.dof_names.index(n) for n in FINGERS], dtype=torch.int32)
        self.left_kin = ArmKin(side="left")
        self.left_kin.scene = world
        self.left_kin.motion = kin.motion
        self.left = torch.tensor([robot.dof_names.index(n) for n in self.left_kin.names[2:]], dtype=torch.int32)
        self.left_fing = torch.tensor([robot.dof_names.index(n) for n in
                                       ("left_gripper_left_finger_axis", "left_gripper_right_finger_axis")], dtype=torch.int32)
        self.left_q_cmd = np.array([LEFT_ARM_FOLD.get(n, 0.0) for n in self.left_kin.names[2:]], float)
        self.left_grip_cmd = 0.04
        self.head = torch.tensor([robot.dof_names.index(n) for n in ("head_yaw_joint", "head_pitch_joint")],
                                 dtype=torch.int32)
        self.head_cmd = np.zeros(2)
        # the base: x, y (m) and yaw (rad) joints of the articulation (physics.base_joints)
        self.base = torch.tensor([robot.dof_names.index(n) for n in BASE_JOINTS], dtype=torch.int32)
        self.base_cmd = self.robot.get_joint_positions()[self.base.long()].cpu().numpy().astype(float)
        self.base_vel = np.zeros(3)
        self.q_cmd = self.q()
        self.last_off = 0.0                     # m the last follow stopped off its command (_settle)
        self.grip_cmd = 0.04
        self.tick, self.stride = 0, stride
        self.frames = []             # JPEG bytes, composed as they are rendered
        self.events, self.caption, self.trace = [], "", []
        self.clear = Clearance(self)        # collision policy of the motions + contact monitor (clearance.py)
        self.tick_watchers = []             # fn() called after every physics tick (skill_jobs.stir: the tip sampled)
        self._scope = False                 # a motion is being planned (_planning)
        self._log = log
        self._arts, self._dof, self._bodies = {}, {}, {}
        by_prim = {}
        for a in ann.articulated:
            # a carcass with several doors/drawers is one articulation, one DOF per part
            if a["prim"] not in by_prim:
                art = SingleArticulation(a["prim"], name=f"art_{len(by_prim)}_{a['prim'].rsplit('/', 1)[-1]}")
                art.initialize()
                by_prim[a["prim"]] = art
            art = by_prim[a["prim"]]
            self._arts[a["name"]] = art
            self._dof[a["name"]] = art.get_dof_index(a["dof"]) if a.get("dof") else 0
        for name, o in ann.objects.items():
            b = SingleRigidPrim(o["body"], name=f"obj_{name}")
            b.initialize()
            b.set_sleep_threshold(OBJECT_SLEEP)          # resting objects sleep (physics.OBJECT_SLEEP)
            self._bodies[name] = b
        # the gripper links' rigid views (sticky hands weld to them), built now: a view built mid-episode
        # puts every object that slept and has moved since back where it fell asleep (physics.OBJECT_SLEEP)
        from .sticky import LINKS
        self.gripper_links = {}
        for hand, path in LINKS.items():
            g = SingleRigidPrim(path, name=f"gripper_link_{hand}")
            g.initialize()
            self.gripper_links[hand] = g
        x, y, yaw = self.base_pose()
        self.kin.set_base((x, y, 0.0), math.radians(yaw))
        self.left_kin.set_base((x, y, 0.0), math.radians(yaw))
        self.held = None
        self.left_held = None
        self.focus_z = None          # follow-camera target height (low for floor picks)
        self.camera_override = None  # optional (eye, target) for a visible appliance action
        from .evaluator import Geometry
        self.geo = Geometry(ann)

        self.thermal = None
        # Facts the robot recorded (seen objects, wiped surfaces ...) and the
        # support each object started on; see predicates.memory().
        self.memory = {"observed": {}, "wiped": {}, "stirred": {}, "explored": {},
                       "initial_support": {n: o.get("support") for n, o in ann.objects.items()},
                       # filled by Episode once the scene has settled; see predicates.memory()
                       "initial_xy": {}}

    def configure_thermal(self, task):
        if task.get("thermal"):
            from .thermal import ThermalModel
            self.thermal = ThermalModel(task["thermal"], sources=task.get("thermal_sources"))

    def _advance_thermal(self, dt):
        if self.thermal is not None:
            self.thermal.step(self, dt)

    # the object in each hand (a dict from the grasp, or None); sticky hands weld it while held
    @property
    def held(self):
        return self.__dict__.get("_held")

    @held.setter
    def held(self, value):
        if self.sticky is not None:
            self.sticky.on_hold("right", value)
        self._held = value

    @property
    def left_held(self):
        return self.__dict__.get("_left_held")

    @left_held.setter
    def left_held(self, value):
        if self.sticky is not None:
            self.sticky.on_hold("left", value)
        self._left_held = value

    # ------------------------------------------------------------ state
    def q(self):
        return self.robot.get_joint_positions()[self.arm.long()].cpu().numpy().astype(float)

    def fingers(self):
        return self.robot.get_joint_positions()[self.fing.long()].cpu().numpy().astype(float)

    def left_q(self):
        arm = self.robot.get_joint_positions()[self.left.long()].cpu().numpy().astype(float)
        return np.r_[self.q()[:2], arm]

    def chain_q(self, side="right"):
        return _chain_q(self, side)

    def chain_cmd(self, side="right"):
        return _chain_cmd(self, side)

    def held_of(self, side="right"):
        return _held_of(self, side)

    def fingers_of(self, side="right"):
        return _fingers_of(self, side)

    def head_q(self):
        v = self.robot.get_joint_positions()[self.head.long()].cpu().numpy().astype(float)
        return {"head_yaw_joint": float(v[0]), "head_pitch_joint": float(v[1])}

    def left_fingers(self):
        return self.robot.get_joint_positions()[self.left_fing.long()].cpu().numpy().astype(float)

    def joint(self, art_name):
        return float(self._arts[art_name].get_joint_positions()[self._dof[art_name]])

    def obj_pose(self, name):
        p, q = self._bodies[name].get_world_pose()
        return p.cpu().numpy().astype(float), q.cpu().numpy().astype(float)

    def base_pose(self):
        x, y, yaw = self.robot.get_joint_positions()[self.base.long()].cpu().numpy().astype(float)
        return float(x), float(y), (math.degrees(yaw) + 180.0) % 360.0 - 180.0

    def state(self):
        """{"objects": {name: {pos, quat}}, "joints": {art: q}} (evaluator format)."""
        objs = {}
        for name in self.ann.objects:
            p, q = self.obj_pose(name)
            objs[name] = {"pos": p.tolist(), "quat": q.tolist()}
        return {"objects": objs, "joints": {a["name"]: self.joint(a["name"]) for a in self.ann.articulated},
                "temperatures_c": dict(self.thermal.temperatures_c) if self.thermal else {}}

    def sync_world(self):
        """Planner/IK model <- simulator: joint values of every articulated
        part, the real base pose (planning moves kin's base around) and the
        free objects low enough to block the base column."""
        for a in self.ann.articulated:
            self.world.set_joint(a["name"], self.joint(a["name"]))
        st = self.state()
        boxes = []
        for name in self.ann.objects:
            if (self.held is not None and name == self.held["name"]) or \
               (self.left_held is not None and name == self.left_held["name"]):
                continue
            b = self.geo.bottom(name, st)
            if b[2] > 0.25 and not self._overhangs(name, st):
                continue
            x0, y0, x1, y1 = self.geo.footprint(name, st, margin=0.01)
            boxes.append([x0, y0, b[2], x1, y1, b[2] + self.ann.asset_of(self.ann.objects[name])["size"][2]])
        self.world.set_base_obstacles(boxes)
        x, y, yaw = self.base_pose()
        self.kin.set_base((x, y, 0.0), math.radians(yaw))
        self.left_kin.set_base((x, y, 0.0), math.radians(yaw))
        self.world.right_kin, self.world.right_q = self.kin, self.q_cmd.copy()
        self.world.left_kin, self.world.left_q = self.left_kin, np.r_[self.q_cmd[:2], self.left_q_cmd]
        if self.kin.motion is not None:
            self.kin.motion.sync(self)

    def _overhangs(self, name, st):
        """Object sticking out past its support's edge (pushed for an edge
        pinch): the base column must not drive into it."""
        p = self.geo.centre(name, st)
        for a in self.ann.articulated:
            b = a.get("body_aabb")
            if b and all(b[i] < p[i] < b[i + 3] for i in range(3)):
                # The cabinet's own collision shape already blocks the base.
                # Counting its contents again creates a phantom obstruction
                # beside the door while the robot follows the hinge.
                return False
        s = self.geo.support_under(name, st)
        if s is None:
            return False
        x0, y0, x1, y1 = self.geo.footprint(name, st)
        sx0, sy0, sx1, sy1 = s["aabb_xy"]
        return x0 < sx0 - 0.01 or y0 < sy0 - 0.01 or x1 > sx1 + 0.01 or y1 > sy1 + 0.01

    def log(self, label, **kw):
        ev = {"tick": self.tick, "t": round(self.tick / PHYSICS_HZ, 3), "label": label, **kw}
        self.events.append(ev)
        self._log("EVENT " + json.dumps(ev, default=float))

    def get_first_person_image(self):
        """Return the current Malo head-camera RGB image as a uint8 H×W×3 copy.

        Rendering happens on demand without advancing physics. Enable the camera
        with ``launch(first_person=True)`` and ``make_rig(..., first_person=True)``.
        """
        if self.first_person_camera is None:
            raise RuntimeError("First-person camera is disabled; pass first_person=True to launch() and make_rig().")
        return self._render(self.first_person_camera)

    def agent_cameras(self):
        """Cameras mounted on the robot, by name: ``head`` and, if enabled, ``left_wrist`` / ``right_wrist``."""
        cams = {"head": self.first_person_camera} if self.first_person_camera is not None else {}
        return {**cams, **self.wrist_cameras}

    def get_camera_images(self):
        """One uint8 H×W×3 RGB image per robot-mounted camera, rendered once without advancing physics."""
        cams = self.agent_cameras()
        if not cams:
            return {}
        self.sim.render()
        return {name: self._read(cam) for name, cam in cams.items()}

    def _render(self, cam):
        self.sim.render()
        return self._read(cam)

    @staticmethod
    def _read(cam):
        cam.update(0.0, force_recompute=True)
        return cam.data.output["rgb"][0, ..., :3].cpu().numpy().copy()

    # ------------------------------------------------------------ stepping
    def step(self, n=1):
        from isaacsim.core.utils.types import ArticulationAction
        t = self.torch
        for _ in range(n):
            # the yaw reading kept in [-pi, pi): PhysX refuses targets of the unlimited yaw joint
            # (eREVOLUTE) beyond +-2 pi, which left the base turned away from where the planner put
            # it, but lets the reading itself run on.  A reading past pi is set back by a turn (the
            # same pose) -- before any drive target of this tick: Isaac's set_joint_positions also
            # sets every joint's drive target to where the joint is now, and after the targets it
            # held whatever was moving that tick.  Parked at 180 deg the reading crosses pi back and
            # forth, so a torso lowering there stalled at -0.35..-0.38 of -0.54 (all 10 lowerings at
            # +-180 deg since this wrap came in, T26 / T05 / T02; none at other yaws, 11-16).
            yaw = float(self.robot.get_joint_positions()[self.base.long()][2])
            if abs(yaw) > math.pi:
                yaw = (yaw + math.pi) % (2 * math.pi) - math.pi
                self.robot.set_joint_positions(t.tensor([yaw], dtype=t.float32), joint_indices=self.base[2:])
            # both arms, both hands and the head: one action (their joints are disjoint; one call per
            # group was 5 of the 6 apply_action calls a tick)
            pos_idx = self.__dict__.get("_pos_idx")
            if pos_idx is None:
                pos_idx = self._pos_idx = t.cat([self.arm, self.fing, self.left, self.left_fing, self.head])
                assert len(set(pos_idx.tolist())) == len(pos_idx), "arm / hand / head joints overlap"
            self.robot.apply_action(ArticulationAction(joint_positions=t.cat([
                t.tensor(self.q_cmd, dtype=t.float32), t.full((2,), float(self.grip_cmd)),
                t.tensor(self.left_q_cmd, dtype=t.float32), t.full((2,), float(self.left_grip_cmd)),
                t.tensor(self.head_cmd, dtype=t.float32)]), joint_indices=pos_idx))
            # the yaw target within half a turn of the joint's reading
            base_q = self.base_cmd.copy()
            base_q[2] = yaw + (base_q[2] - yaw + math.pi) % (2 * math.pi) - math.pi
            self.robot.apply_action(ArticulationAction(joint_positions=t.tensor(base_q, dtype=t.float32),
                                                       joint_velocities=t.tensor(self.base_vel, dtype=t.float32),
                                                       joint_indices=self.base))
            self.base_vel = np.zeros(3)         # a set_base each tick keeps the base moving
            self._payload_feedforward()
            render = bool(self.cams) and self.tick % self.stride == 0
            self.sim.step(render=render)
            self.tick += 1
            if self.tick % 12 == 0:
                self._advance_thermal(0.1)
            if self.clear.monitor:
                self.clear.every_tick()
                if self.tick % MONITOR_EVERY == 0:
                    self.clear.tick()
            for watch in self.tick_watchers:      # a skill's own measurement while a segment runs (stir's turns)
                watch()
            if render:
                imgs = []
                for cam in self.cams.values():
                    cam.update(1 / PHYSICS_HZ)
                    imgs.append(cam.data.output["rgb"][0, ..., :3].cpu().numpy())
                self.frames.append(self._compose(imgs, self.caption))

    def wake(self, name):
        """Wake object ``name``'s body: a pose or velocity written into a sleeping body need not wake
        it, and asleep it would hang where it was put (sticky's snap and place teleport objects)."""
        w = self.__dict__.get("_waker")
        if w is None:
            import omni.usd
            from omni.physx import get_physx_simulation_interface
            from pxr import PhysicsSchemaTools
            sim, sid, to_int = (get_physx_simulation_interface(), omni.usd.get_context().get_stage_id(),
                                PhysicsSchemaTools.sdfPathToInt)
            w = self._waker = lambda body: sim.wake_up(sid, to_int(body))
        w(self.ann.objects[name]["body"])

    def _payload_mass(self, name):
        """(kg, centre of mass in the body frame) of object ``name`` as PhysX has it (cached)."""
        cache = self.__dict__.setdefault("_payload_cache", {})
        if name not in cache:
            b = self._bodies[name]
            com, _ = b.get_com()
            com = com.cpu().numpy() if hasattr(com, "cpu") else np.asarray(com)
            m = b.get_mass()
            cache[name] = (float(m.item() if hasattr(m, "item") else m), np.asarray(com, float).reshape(3))
        return cache[name]

    def _payload_feedforward(self):
        """The held loads' weight carried by joint torques on top of the position drives (payload_torques),
        set before every physics step: one hand's load on its chain; a bimanual hold half on each.  The
        torso and the waist, shared by both chains, take the sum.  Zero when nothing is held."""
        h, lh = getattr(self, "held", None), getattr(self, "left_held", None)
        if h and h.get("kind") == "bimanual":
            loads = [("right", h.get("name"), 0.5), ("left", h.get("name"), 0.5)]   # (side, name, share)
        else:
            loads = [(s, x.get("name"), 1.0) for s, x in (("right", h), ("left", lh)) if x and x.get("kind") != "part"]
        right, left = np.zeros(len(self.kin.names)), np.zeros(len(self.left_kin.names))
        on = {}
        for side, name, share in loads:
            if name not in self._bodies:
                continue
            kin = self.kin if side == "right" else self.left_kin
            q = _chain_q(self, side)
            mass, com_b = self._payload_mass(name)
            p, quat = self.obj_pose(name)
            com = p + _quat_R(quat) @ com_b
            if np.linalg.norm(com - kin.tcp(q)[0]) > PAYLOAD_REACH:
                continue
            tau = payload_torques(kin, q, com, mass * share)
            if side == "right":
                right += tau
            else:
                left += tau
            on[side] = (name, round(mass * share, 3))
        right[:2] += left[:2]                           # the body both chains ride on
        if not on and not getattr(self, "_payload_on", None):
            return                                      # nothing held, and nothing set before
        if on != getattr(self, "_payload_on", None):
            self.log("payload_feedforward", loads={s: {"obj": n, "kg": m} for s, (n, m) in on.items()},
                     tau_right=np.round(right, 3).tolist(), tau_left=np.round(left[2:], 3).tolist())
        self._payload_on = on
        t = self.torch
        # one call: set_joint_efforts writes every DOF's actuation force, the ones not named zero (a second
        # call for the left arm cleared the right's -- liftdbg_1112 ran with no feedforward at all)
        self.robot.set_joint_efforts(t.tensor(np.r_[right, left[2:]], dtype=t.float32),
                                     joint_indices=t.cat([self.arm, self.left]))

    def _held_container(self, side="right"):
        """The hand holds a container (by its rim: it hangs off a thin wall)."""
        h = _held_of(self, side)
        if h is None or h.get("kind") == "bimanual" or h.get("name") not in self.ann.objects:
            return False
        return bool(self.ann.asset_of(self.ann.objects[h["name"]]).get("container"))

    def _drive_cap(self):
        """drive_base's speed cap for what the hands hold: a container hanging off a thin wall in a
        one-hand rim pinch pivots under base accelerations, and so does a load in the left hand
        alone (after a handover: a full-speed drive shook a rolling pin out)."""
        if self._held_container() or (getattr(self, "left_held", None) is not None and self.held is None):
            return DRIVE_SWINGING
        return DRIVE_LOADED if self.held is not None else DRIVE_EMPTY

    def _vmax(self, side="right"):
        """Joint speeds ``side``'s paths are executed at: 60% of the URDF limits (torso lift is 0.117 m/s;
        ignoring this was a 0.29 m tracking error); with an object in the hand the arm joints at
        most CARRY_VEL (RIM_VEL for a rim-held container) so it is not flung.  (The other hand's
        load rides the body only, which stays put while that hand holds it: docs 4.1.)"""
        v = 0.6 * vel_limits((self.kin if side == "right" else self.left_kin).names)
        if self._carrying(side):
            v[2:] = np.minimum(v[2:], RIM_VEL if self._held_container(side) else CARRY_VEL)
        return v

    def follow_smooth(self, qs, steps_per_wp=3, settle=150, tol=0.01, side="right"):
        """Follow the same planned joint waypoints with a gentle start and stop.

        Time scaling only changes progress along the existing joint segments;
        it never rounds a corner into a configuration outside that path.
        """
        self.clear.executing()
        points = [_chain_cmd(self, side)] + [np.asarray(q, float) for q in qs]
        if len(points) == 1:
            self.last_off = 0.0
            return 0.0
        vmax = self._vmax(side)
        segment_times = [max(steps_per_wp / PHYSICS_HZ,
                             float(np.max(np.abs(b - a) / vmax)))
                         for a, b in zip(points[:-1], points[1:])]
        times = np.r_[0.0, np.cumsum(segment_times)]
        path_time = float(times[-1])
        ramp = min(0.8, path_time / 2)
        duration = path_time + ramp
        ticks = max(2, int(math.ceil(duration * PHYSICS_HZ)))
        for i in range(1, ticks + 1):
            t = duration * i / ticks
            if t < ramp:
                progress = 0.5 * (t - ramp / math.pi * math.sin(math.pi * t / ramp))
            elif t < path_time:
                progress = t - ramp / 2
            else:
                remaining = duration - t
                progress = path_time - 0.5 * (remaining - ramp / math.pi * math.sin(math.pi * remaining / ramp))
            segment = min(len(segment_times) - 1, int(np.searchsorted(times, progress, side="right") - 1))
            fraction = min(1.0, max(0.0, (progress - times[segment]) / segment_times[segment]))
            _set_chain_cmd(self, side, points[segment] + fraction * (points[segment + 1] - points[segment]))
            self.step(1)
        return self._settle(settle, tol, side)

    def _settle(self, settle, tol, side="right"):
        """After a follow's last command: step (2 ticks at a time, ``settle`` times at most) until the
        arm has arrived -- the TCP within SETTLE_TCP of where q_cmd puts it and no joint off by
        ``tol`` -- or has stopped: the TCP moved less than SETTLE_STILL over the last SETTLE_WINDOW
        ticks.  Returns how far (m) the TCP stands off where q_cmd puts it: the caller judges it (run: a
        segment that stopped further off than TARGET_TOL is blocked; Rig.move_to: its reach check)."""
        kin, cmd = (self.kin if side == "right" else self.left_kin), _chain_cmd(self, side)
        target = kin.tcp(cmd)[0]
        span = max(1, SETTLE_WINDOW // 2)
        seen = []
        for _ in range(settle):
            q = _chain_q(self, side)
            tcp = kin.tcp(q)[0]
            if np.linalg.norm(tcp - target) < SETTLE_TCP and np.max(np.abs(q - cmd)) < tol:
                self.last_off = float(np.linalg.norm(tcp - target))
                return self.last_off
            seen.append(tcp)
            if len(seen) > span and np.linalg.norm(tcp - seen[-1 - span]) < SETTLE_STILL * 2 * span / PHYSICS_HZ:
                break
            self.step(2)
        q = _chain_q(self, side)
        off = float(np.linalg.norm(kin.tcp(q)[0] - target))
        if np.max(np.abs(q - cmd)) > SETTLE_OFF_LOG:      # stopped off the command: which joints
            self.log("settle_off", side=side, q=np.round(q, 3).tolist(), q_cmd=np.round(cmd, 3).tolist(),
                     tcp_err_m=round(off, 4), carrying=bool(self._carrying(side)))
        self.last_off = off                      # (the last follow's: what a skill's hook judges after it)
        return off

    def follow(self, qs, steps_per_wp=3, settle=150, tol=0.01, smooth=False, side="right"):
        """Waypoints time-scaled to the joint speeds of _vmax; with an object in the hand (or
        ``smooth``) always follow_smooth's gentle start and stop (a jerk shakes it out of the pinch).
        ``side``: whose waypoints (its planning chain, torso and waist first) -- the same execution
        for either arm (the old left_follow stays for the old entries)."""
        if smooth or self._carrying(side):
            return self.follow_smooth(qs, steps_per_wp, settle, tol, side=side)
        self.clear.executing()
        vmax = self._vmax(side)
        for q in qs:
            q = np.asarray(q, float)
            need = int(math.ceil(np.max(np.abs(q - _chain_cmd(self, side)) / vmax) * PHYSICS_HZ))
            _set_chain_cmd(self, side, q)
            self.step(max(steps_per_wp, need))
        return self._settle(settle, tol, side)

    # ------------------------------------------------------------ arm motions
    # Every arm motion has two ways (docs/motion/COLLISION_PLAN.md principle 2): collision-checked, the
    # straight move when it is free, else a planned trajectory; unchecked, the straight move.
    # A checked motion with a fallback Allow that finds no path makes the unchecked one, logged.
    def move_to(self, p, R, step=0.01, steps_per_wp=3, label=None, allow=FREE, q_hint=None,
                smooth=False, approach=None, free=FREE_ELSE_STRAIGHT):
        """Move the TCP to (p, R): the straight line, else a planned trajectory (_move_path).
        ``q_hint``: a joint solution of the target (find_park's), the planner's joint goal.
        ``allow`` (clearance.Allow): what the move may touch (_motion_path).
        ``approach`` (u, L[, q_line]): the move ends with the straight line of length L along the
        unit direction u to (p, R) -- a grasp, a load set down -- and ``allow`` is either the
        into_contact Allow of the contact segment it ends in, or a checked Allow: then (p, R) must be
        clear of the world and the whole approach is checked (an open hand around what it will pinch);
        (_approach); ``free`` the Allow of the planned part before it; ``q_line`` a joint solution
        of the line's start (find_park's, which checked the unfold to it with the tilt held)."""
        self.sync_world()
        p = np.asarray(p, float)
        follow = lambda qs: (self.follow_smooth if smooth else self.follow)(qs, steps_per_wp)
        if approach is not None and (allow.to_contact or allow.checked) and self.kin.scene is not None \
                and self.kin.motion is not None:
            self._approach(p, R, approach, step, label, q_hint, allow, free, follow)
        elif self._exits_contact(allow, self.kin):
            with self._lifting(self.kin, allow):
                if self._leave_contact(label, allow, self.kin,
                                       lambda: self._straight_move(p, R, step, label, q_hint), follow):
                    return self.move_to(p, R, step, steps_per_wp, label, FREE_ELSE_STRAIGHT, q_hint, smooth)
        else:
            qs, allow = self._motion_path(label, allow, self.kin, lambda: self._move_path(p, R, step, label, q_hint),
                                          lambda: self._straight_move(p, R, step, label, q_hint))
            self.clear.motion(label, allow)
            follow(qs)
        tcp, _ = self.kin.tcp(self.q())
        err = float(np.linalg.norm(tcp - p))
        qe = self.q() - self.q_cmd
        extra = {}
        if np.max(np.abs(qe)) > 0.05:
            extra = {"q": np.round(self.q(), 3).tolist(), "q_cmd": np.round(self.q_cmd, 3).tolist()}
        self.log("reach", target=label, tcp_err_m=round(err, 4), q_err=round(float(np.max(np.abs(qe))), 4), **extra)
        return err


    def move_to_any(self, goals, step=0.01, steps_per_wp=3, label=None, allow=FREE, smooth=False, cost=None,
                    prefer=None, weights=None):
        """Move the TCP to the goal of the set ``goals`` [(p, R)] the arm gets to most cheaply: one
        batched IK of all of them (collision-free solutions near the current posture, the held
        object in the collision model: Kinematics.ik_set), the reachable goal of least joint
        travel plus ``cost[i]`` (rad), then move_to it with its solution as the joint goal.  The
        goals are not tried one after another: the choice is made before the arm moves, and
        what happens after it is that one motion's (SkillFailure, or ``allow``'s fallback).
        ``prefer``: the posture the IK solutions are sought near and the travel is measured from
        (default the current one; a carry pose stands the body up), ``weights`` per joint on that
        distance.  Returns the chosen index; SkillFailure when no goal has a solution."""
        if not goals:
            raise SkillFailure(f"{label}: empty goal set")
        self.sync_world()
        cost = np.zeros(len(goals)) if cost is None else np.asarray(cost, float)
        ref = self.q_cmd if prefer is None else np.asarray(prefer, float)
        w = np.ones(len(ref)) if weights is None else np.asarray(weights, float)
        with self._planning(self.kin, self.q_cmd):
            qs = self.kin.ik_set(goals, ref, weights=w)
        score = np.array([np.inf if q is None else float(np.max(np.abs(q - ref) * w)) + c
                          for q, c in zip(qs, cost)])
        i = int(np.argmin(score))
        self.log("goal_set", target=label, goals=len(goals), reachable=int(np.isfinite(score).sum()),
                 chosen=i if np.isfinite(score[i]) else None,
                 score=[None if not np.isfinite(v) else round(float(v), 3) for v in score],
                 q_start=np.round(self.q_cmd, 3).tolist(),
                 q_goal=None if qs[i] is None else np.round(qs[i], 3).tolist())
        if not np.isfinite(score[i]):
            raise SkillFailure(f"{label}: no goal of {len(goals)} reachable")
        p, R = goals[i]
        self.move_to(p, R, step, steps_per_wp, label, allow, q_hint=qs[i], smooth=smooth)
        return i

    def leave(self, u, label, allow, step=0.004, smooth=True, steps_per_wp=3, lifts_off=False):
        """Out of the contact the hand starts in along the unit direction ``u`` (up off a support,
        out of a shelf): the contact segment of a from_contact ``allow`` (LEAVE_CONTACT, lifting),
        as long as the collision model says the robot touches the world (_leave_contact, at most
        LEAVE_MAX); no end pose -- the next relay pose is planned from where it ends.  ``lifts_off``:
        the hand lifts its load off a support (_leave_contact)."""
        if not allow.from_contact:
            raise ValueError("leave is for a from_contact Allow")
        self.sync_world()
        tcp, R = self.kin.tcp(self.q_cmd)
        u = np.asarray(u, float) / np.linalg.norm(u)
        # as far along u as the arm reaches (an arm stretched to a far spot has no 6 cm up): the
        # straight move is computed once, the contact exit measured on it (two separate IK calls
        # disagree, cuRobo's IK is seeded at random: T09)
        d, line = LEAVE_MAX, None
        while d >= LEAVE_MARGIN and line is None:
            try:
                line = self._straight_move(tcp + d * u, R, step, label, None)
            except SkillFailure:
                d /= 2
        if line is None:
            self.log("leave_contact_exit", target=label, exit_m=0.0, waypoints=0, of=0, clear=False,
                     why="no IK along the exit")
            return
        follow = lambda qs: (self.follow_smooth if smooth else self.follow)(qs, steps_per_wp)
        straight = lambda: line
        # the fingers too: the next relay pose is planned with them (docs/motion/COLLISION_PLAN.md, 3b)
        with self._lifting(self.kin, allow), self._fingers_checked(self.kin):
            if self._exits_contact(allow, self.kin):
                self._leave_contact(label, allow, self.kin, straight, follow, lifts_off=lifts_off)
            else:
                self.clear.motion(label, allow)
                follow(straight())

    def _approach(self, p, R, approach, step, label, q_hint, allow, free, follow):
        """move_to with an approach (u, L): the contact at (p, R) entered straight along u -- its
        segment as long as the robot, its fingers and its load touch the world there going back
        along u (_exit_length on that line, at most LEAVE_MAX), unchecked under ``allow`` -- and
        before it the free motion to where that segment starts, planned with the fingers in the
        collision model to end with the straight line of length L along u (_approach_path;
        ``free`` its Allow: no path -> its fallback, or SkillFailure).  A checked ``allow`` (no
        contact segment): (p, R) itself clear by the caller's coll_kw, else SkillFailure."""
        kin = self.kin
        u = np.asarray(approach[0], float) / np.linalg.norm(approach[0])
        L = float(approach[1])
        q_line = approach[2] if len(approach) > 2 else None
        # the contact pose clear of the world by the contact's own rule (the caller's coll_kw: the
        # fingers out, the target exempt), so the segment's contact is the fingers' and the load's
        # alone: an unchecked solution put the gripper into the island and the segment drove it
        # there, 2 cm short of the grasp (T10, P15)
        seeds = [np.asarray(q_hint, float)] if q_hint is not None else []
        with self._planning(kin, self.q_cmd, keep_held=True):
            q_p, ok = kin.ik_global(p, R, seeds=seeds + [self.q_cmd])
        if not ok:
            if not allow.to_contact:
                raise SkillFailure(f"{label}: no collision-free IK at the end pose")
            q_p = self._ik_unchecked(p, R, q_hint, label)
        with self._fingers_checked(kin):
            back = self._line_unchecked(q_p, p - LEAVE_MAX * u, R, step)
            with self._planning(kin, self.q_cmd, keep_held=True):
                n, clear = self._exit_length(kin, q_p, back, touching=lambda q: not kin.free(q))
            q_c = back[n - 1] if n else q_p
            entry = back[:n - 1][::-1] + [q_p] if n else []
            p_c = kin.tcp(q_c)[0]
            entry_m = float(np.linalg.norm(p_c - p))
            self.log("contact_entry", target=label, entry_m=round(entry_m, 4), clear=clear)
            if entry and not allow.to_contact:
                with self._planning(kin, self.q_cmd, keep_held=True):
                    why = kin.explain(q_p)
                raise SkillFailure(f"{label}: the end pose touches the world ({why})")

            def plan():
                if not clear:
                    raise SkillFailure(f"{label}: the contact lasts {LEAVE_MAX} m back along the approach")
                # the last L of the approach straight: the contact segment is part of it
                return self._approach_path(q_c, R, u, max(0.0, L - entry_m), step, label, q_line)
            qs, a = self._motion_path(label, free, kin, plan, lambda: self._straight_move(p_c, R, step, label, q_c))
        self.clear.motion(label, a)
        follow(qs)
        if entry:
            self.clear.motion(label, self._into_contact(kin, allow))
            follow(entry)

    def _approach_path(self, q_c, R, u, L, step, label, q_line=None):
        """Collision-checked waypoints from q_cmd to q_c ending with the straight line of length L
        along u: straight when the TCP is on that line already; else to the line's start
        (_move_path: the straight line, the planner -- a load's tilt held -- or its joint goal,
        q_line, find_park's solution there, as the hint) and along it -- as cuRobo's own plan_grasp
        does.  Not one trajectory with the line as a cost (Arm.approach_metric's kind): it bends at
        the end, and a pinch so planned pushed a bowl 2.5 cm and stopped 4.4 cm short (T20)."""
        kin = self.kin
        p_c = kin.tcp(q_c)[0]
        d = p_c - kin.tcp(self.q_cmd)[0]
        along = float(d @ u)
        if -1e-3 <= along <= L + 1e-3 and np.linalg.norm(d - along * u) < ON_LINE:
            qs, ok = kin.cart_path(self.q_cmd, p_c, R, step=step)
            if ok:
                self.log("straight_leg", target=label, exempt=getattr(kin.motion, "exempt", None))
                return qs
        if L < ON_LINE:
            return self._move_path(p_c, R, step, label, q_line if q_line is not None else q_c)
        s = p_c - L * u
        first = self._move_path(s, R, step, label, q_line if q_line is not None else q_c)
        rest, ok = kin.cart_path(first[-1], p_c, R, step=step)
        if not ok:
            scene, kin.scene = kin.scene, None
            try:
                line, free_ik = kin.cart_path(first[-1], p_c, R, step=step)
                why = "it collides" if free_ik else "no IK along it"
            finally:
                kin.scene = scene
            at = next((i for i, q in enumerate(line) if not kin.free(q)), None) if free_ik else None
            if at is not None and hasattr(kin.motion, "contacts_by_owner"):
                # where along the line and into what (by owner, every link checked)
                self.log("approach_line_hit", target=label, at=round(at / max(len(line) - 1, 1), 2),
                         by_owner=kin.motion.contacts_by_owner(kin, line[at], kin._other_q()))
            raise SkillFailure(f"{label}: no collision-free straight approach from its start ({why}: "
                               f"{kin.explain(first[-1]) if not kin.free(first[-1]) else 'start clear'})")
        self.log("planned_leg", target=label, how="line_start", waypoints=len(first) + len(rest),
                 carry=self._carrying())
        return first + rest

    @contextmanager
    def _fingers_checked(self, kin):
        """The motions inside as free space for ``kin``'s hand (FREE_SPACE_KW): its fingers in the
        collision model, and the objects at their TCP targets too (the approach's own contact
        segment is where it may touch them)."""
        kw = kin.coll_kw
        kin.coll_kw = {**{k: v for k, v in kw.items() if k != "ignore_fingers"}, **FREE_SPACE_KW}
        try:
            yield
        finally:
            kin.coll_kw = kw

    def _ik_unchecked(self, p, R, q_hint, label):
        """A kinematic IK solution of (p, R) near q_hint / the current posture, the world left out
        (a contact pose touches it), or SkillFailure."""
        scene, self.kin.scene = self.kin.scene, None
        try:
            seeds = [np.asarray(q_hint, float)] if q_hint is not None else []
            q, ok = self.kin.ik_global(p, R, seeds=seeds + [self.q_cmd])
        finally:
            self.kin.scene = scene
        if not ok:
            raise SkillFailure(f"no IK for {label or p}")
        return np.asarray(q, float)

    def _line_unchecked(self, q0, p, R, step):
        """The straight TCP line from q0 to (p, R) as joint waypoints, the world left out (shorter
        where the IK runs out along it)."""
        scene, self.kin.scene = self.kin.scene, None
        try:
            qs, ok = self.kin.cart_path(q0, p, R, step=step)
        finally:
            self.kin.scene = scene
        return list(qs) if qs else []

    def _into_contact(self, kin, allow):
        """An into_contact Allow for ``kin``'s hand."""
        return replace(allow, hand=kin.side) if allow.hand is None else allow

    def _start(self, kin):
        return self.q_cmd if kin is self.kin else np.r_[self.q_cmd[:2], self.left_q_cmd]

    def _motion_path(self, label, allow, kin, plan, straight):
        """(waypoints, the Allow they run under) of one motion of ``kin``'s arm.  Unchecked (or no
        world): ``straight()``.  Checked: ``plan()`` inside _planning; when that finds no path --
        or, for a fallback Allow, the arm already starts in collision -- a fallback Allow makes
        ``straight()`` and logs a clearance_fallback with what that path runs into, any other
        raises SkillFailure."""
        if not allow.checked or kin.scene is None:
            return straight(), self._from_contact(kin, allow)
        start = self._start(kin)
        with self._planning(kin, start):
            if allow.fallback and not kin.free(start):
                why = "starts in collision: " + kin.explain(start)
            else:
                try:
                    qs = plan()
                    if allow.fallback:
                        self.clear.planned(label)
                    return qs, allow
                except SkillFailure as exc:
                    if not allow.fallback:
                        raise
                    why = str(exc)
                    self.log("plan_failed", target=label, why=why)
        qs = straight()
        with self._planning(kin, start):
            at = next((i for i in list(range(0, len(qs), 5)) + [len(qs) - 1] if not kin.free(qs[i])), None)
            hit = None if at is None else kin.explain(qs[at])
            if at is not None and hasattr(kin.motion, "contacts_by_owner"):
                # where along the straight path and into what (by owner, every link checked)
                self.log("fallback_hit", target=label, at=round(at / max(len(qs) - 1, 1), 2),
                         by_owner=kin.motion.contacts_by_owner(kin, qs[at], kin._other_q()))
        self.clear.fallback(label, why, hit)
        return qs, LEGACY

    @contextmanager
    def _planning(self, kin, start, keep_held=False):
        """Query state for planning one motion of ``kin``'s arm from ``start``: what that hand holds
        is in the collision model (Motion.scope).  Nested: the outer state stands."""
        motion = kin.motion
        if motion is None or getattr(self, "_scope", False):
            yield
            return
        self._scope = True
        try:
            with motion.scope(self, kin, start, keep_held=keep_held):
                yield
        finally:
            self._scope = False

    @contextmanager
    def _lifting(self, kin, allow):
        """While a motion lifts an object the hand has closed on but that is not held yet
        (``allow.lifts``: pick checks the lift before it records the hold), the object rides in
        the hand's collision model like a held one (motion.load): no obstacle where it stood, and
        the contact exit ends once it is clear of its support."""
        if allow.lifts is None:
            yield
            return
        self.lifting = {**getattr(self, "lifting", {}), kin.side: {"name": allow.lifts, "kind": "pinch"}}
        try:
            self.sync_world()
            yield
        finally:
            self.lifting = {s: h for s, h in self.lifting.items() if s != kin.side}
            self.sync_world()

    @staticmethod
    def _exits_contact(allow, kin):
        """A from_contact motion (clearance.LEAVE_CONTACT) with a collision model to tell where
        its contact ends (_leave_contact); without one it is the whole straight move."""
        return allow.from_contact and kin.scene is not None and kin.motion is not None

    def _leave_contact(self, label, allow, kin, straight, follow, lifts_off=False):
        """The contact segment of a from_contact motion: its straight waypoints only up to
        LEAVE_MARGIN past where the arm, its hand and what the hand holds first come LEAVE_GAP clear
        of the world (none when they start that clear), at most LEAVE_MAX of TCP travel; run under the
        from_contact Allow.  True when the target is still ahead: the caller moves on to it from
        here as a free-space motion (planned; still touching at LEAVE_MAX, the logged straight).
        ``lifts_off``: the load stands on its support at the start -- it touches it until the hand
        has risen LEAVE_GAP, whatever the model says (its spheres sit inside its box: 65 of 252
        lifts read "clear" at once, and a carry that went sideways from there dragged the can, T10)."""
        start = self._start(kin)
        qs = straight()
        z0 = kin.tcp(start)[0][2]
        with self._planning(kin, start, keep_held=True):
            n, clear = self._exit_length(kin, start, qs, touching=(
                lambda q: kin.tcp(q)[0][2] - z0 < LEAVE_GAP or kin.near(q, LEAVE_GAP)) if lifts_off else None)
        allow = self._from_contact(kin, allow)
        p0, p1 = kin.tcp(start)[0], kin.tcp(qs[n - 1] if n else start)[0]
        self.log("leave_contact_exit", target=label, exit_m=round(float(np.linalg.norm(p1 - p0)), 4),
                 waypoints=n, of=len(qs), clear=clear)
        if n:
            self.clear.motion(label, allow, side=kin.side)
            follow(qs[:n])
        return n < len(qs)

    @staticmethod
    def _exit_length(kin, start, qs, touching=None):
        """primitives.exit_length (the one measure of a contact's extent)."""
        return exit_length(kin, start, qs, touching)

    # ---------------------------------------------------- motion_state.Actuator (run.py's only door)
    def snapshot(self):
        """The State now (motion_state.State): the base, the commanded arm postures, the head, each
        hand's finger opening (the wider finger, as Motion.live_locks) and what it holds (its box
        frame in the TCP frame, Motion.held_in_tcp, both as they really stand: the hand at the arm's
        measured joints, not its command -- a load sags the arm and a contact pushes it off its
        command, and a hold read against the commanded TCP would take that for the load moving in the
        hand; welded or not, the measured hold is the one the hand has), the objects' box frames and
        the parts' joint values, all as synced into the collision model (sync_world)."""
        from .kinematics import FINGER_OPEN
        from .motion_state import Hand, Held, State
        self.sync_world()
        motion = self.kin.motion
        hands = {}
        handle = getattr(self, "_handle_grasp", None)
        for side, kin, q, held, fingers in (
                ("right", self.kin, self.q, self.held, self.fingers),
                ("left", self.left_kin, self.left_q, self.left_held, self.left_fingers)):
            width = float(np.clip(np.asarray(fingers(), float)[:2].max(), 0.0, FINGER_OPEN))
            h = None
            if held is not None:
                name = held["name"]
                T = motion.held_in_tcp(kin, q(), name) if motion is not None and motion.by_owner.get(f"object:{name}") \
                    else np.eye(4)
                h = Held(name, T, held.get("kind", "pinch"))
            elif handle is not None and handle.get("side", "right") == side:
                # a handle in this hand (skill_jobs.door, policies GraspArticulatedHandle): the part
                # frame in the TCP frame at the measured joints
                a = self.ann.art(handle["name"])
                p, R = kin.tcp(q())
                T_tcp = np.eye(4)
                T_tcp[:3, :3], T_tcp[:3, 3] = R, p
                h = Held(handle["name"], np.linalg.inv(T_tcp) @ self.ann.part_pose(a, self.joint(handle["name"])),
                         "part")
            hands[side] = Hand(width=width, held=h)
        return State(base=tuple(self.base_pose()), body=np.asarray(self.q_cmd, float)[:2].copy(),
                     arms={"right": np.asarray(self.q_cmd, float)[2:].copy(),
                           "left": np.asarray(self.left_q_cmd, float).copy()}, head=dict(self.head_q()), hands=hands,
                     objects=motion.object_frames() if motion is not None else {},
                     parts={a["name"]: self.joint(a["name"]) for a in self.ann.articulated})

    def arm_kin(self, side="right"):
        return self.kin if side == "right" else self.left_kin

    def ride(self, part, base_at, s_from, s_to, label, lead, rate, done):
        """The closed loop of a task segment that carries the base (motion_state.Actuator.ride, docs
        5.5): each tick the base at ``base_at(cmd)`` -- the script's own function (primitives.ride_base),
        evaluated at the control rate, never off it -- for the commanded part value ``cmd``, which
        advances at most ``rate`` per second toward the measured value + ``lead`` and stays within
        [s_from, s_to].  The arms hold their commands; the grasped handle is all that moves the part.
        Stops with done when the part reaches ``done``; without when it drops back RIDE_SLIP_LEADS leads
        behind ``cmd`` (the handle slipped), stalls (RIDE_STALL over RIDE_STALL_CHECKS checks) or runs
        RIDE_TICKS.  Logs
        ``ride`` every RIDE_LOG_EVERY ticks and ``ride_end``: the lag and the base's distance from its
        command at most (the data a task segment's margin would be set by, docs 8.2)."""
        slip = RIDE_SLIP_LEADS * lead
        sign = 1.0 if s_to > s_from else -1.0
        self.clear.executing()
        lo, hi = min(s_from, s_to), max(s_from, s_to)
        cmd = float(np.clip(self.joint(part), lo, hi))
        last, stall, lag_max, base_err = cmd, 0, 0.0, 0.0
        out = {"done": False, "why": f"{part} did not reach {done:.3f} in {RIDE_TICKS} ticks"}
        for it in range(RIDE_TICKS):
            s = self.joint(part)
            if sign * (done - s) <= 0:
                out = {"done": True}
                break
            lag = sign * (cmd - s)
            lag_max = max(lag_max, lag)
            if lag > slip:
                out = {"done": False, "why": f"{part} dropped back {lag:.3f} behind the command (slipped)"}
                break
            target = float(np.clip(s + sign * lead, lo, hi))
            cmd += float(np.clip(target - cmd, -rate / PHYSICS_HZ, rate / PHYSICS_HZ))
            b = base_at(cmd)
            self.set_base(*b)
            self.step(1)
            x, y, _ = self.base_pose()
            base_err = max(base_err, math.hypot(x - b[0], y - b[1]))
            if it % RIDE_LOG_EVERY == 0:
                hand = (getattr(self, "_handle_grasp", None) or {}).get("side", "right")
                self.log("ride", target=label, s=round(s, 4), cmd=round(cmd, 4), lag=round(lag, 4),
                         fingers=[round(v, 4) for v in _fingers_of(self, hand)])
                if it and abs(s - last) < RIDE_STALL:
                    stall += 1
                    if stall >= RIDE_STALL_CHECKS:
                        out = {"done": False, "why": f"{part} stalled at {s:.3f}"}
                        break
                else:
                    stall = 0
                last = s
        out.update(s=self.joint(part), lag_max=round(lag_max, 4), base_err_max=round(base_err, 4), ticks=it + 1)
        self.log("ride_end", target=label, part=part, **{k: (round(v, 4) if isinstance(v, float) else v)
                                                          for k, v in out.items()})
        return out

    def wait(self, ticks):
        """The world settles ``ticks`` physics ticks, the drives holding their commands (a wait segment)."""
        self.step(int(ticks))

    def aim_head(self, yaw, pitch, steps=90):
        """The head to (yaw, pitch) rad (a head action segment): the command set, then at most ``steps``
        physics ticks, in tens, until both head joints are within HEAD_AT of it."""
        self.head_cmd = np.array([float(yaw), float(pitch)])
        for _ in range(int(steps) // 10):
            self.step(10)
            hq = self.head_q()
            if abs(hq["head_yaw_joint"] - yaw) < HEAD_AT and abs(hq["head_pitch_joint"] - pitch) < HEAD_AT:
                break

    def declare(self, name, allow, side="right", follows=True):
        """The next motion to the contact monitor (Clearance.motion)."""
        self.clear.motion(name, allow, side=side, follows=follows)

    def contact_allow(self, kin, allow):
        return self._from_contact(kin, allow)

    def _from_contact(self, kin, allow):
        """A from_contact Allow (clearance.LEAVE_CONTACT) with what ``kin``'s hand and its load touch
        now -- as the contact monitor sees it -- as its touch / held_on; any other unchanged."""
        if not allow.from_contact or kin.motion is None:
            return allow
        side = kin.side
        h = self.held if side == "right" else getattr(self, "left_held", None)
        hand = {f"{side}_{l}" for l in HAND_LINKS}
        touch, held_on = set(), set()
        for link, entity, _ in kin.motion.robot_contacts(self):
            if link in hand:
                touch.add(entity)
            elif h is not None and link == f"held:{h['name']}":
                held_on.add(entity)
        self.log("leave_contact", side=side, touch=sorted(touch), held_on=sorted(held_on))
        return replace(allow, hand=side, links="hand", touch=allow.touch + tuple(sorted(touch)),
                       held_on=allow.held_on + tuple(sorted(held_on)))

    def _move_path(self, p, R, step, label, q_hint):
        """move_to's collision-checked waypoints: the straight TCP line, else Motion.plan_to (the
        pose under constraints, else the joint goal of _goal)."""
        qs, ok = self.kin.cart_path(self.q_cmd, p, R, step=step)
        if ok:
            self.log("straight_leg", target=label, exempt=getattr(self.kin.motion, "exempt", None))
            return qs
        carry = self._carrying()
        qs, how = self.kin.plan_to(self.q_cmd, p, R, carry=carry, q_goal=self._goal(p, R, q_hint))
        if qs is None:
            raise SkillFailure(f"no collision-free path to {label or p}: {how}")
        self.log("planned_leg", target=label, how=how, waypoints=len(qs), carry=carry,
                 exempt=getattr(self.kin.motion, "exempt", None))
        return self.joint_path_via(qs)

    def _goal(self, p, R, q_hint):
        """Joint goal for a planned leg to (p, R).  With ``q_hint`` (the solution a park search
        validated, the arm's branch to keep): q_hint itself while it still reaches (p, R) within
        HINT_REACH / HINT_TURN and is collision-free (the base stopped where the search put it:
        the goal the search planned to), else q_hint re-solved at the actual base on its branch,
        else None -- no solution on another branch.  Without one: a collision-free IK solution
        near the current posture.  Not re-solved needlessly: a re-solve 0.6 mrad off the hint, its
        waist 1 mrad inside the limit, planned 1 time in 4 where the hint planned 4 in 4 (T04
        no_cup mug; the planner's weakness near a joint limit, plan section 7)."""
        if q_hint is None:
            q, ok = self.kin.ik_global(p, R, seeds=[self.q_cmd])
            return q if ok else None
        q_hint = np.asarray(q_hint, float)
        if near_pose(*self.kin.tcp(q_hint), p, R) and self.kin.free(q_hint):    # decide_ik's step 1
            return q_hint
        q, ok = self.kin.ik(p, R, q_hint)
        return q if ok and self.kin.free(q) else None

    def _straight_move(self, p, R, step, label, q_hint):
        """move_to's unchecked waypoints: the straight TCP line, else (no IK along it) the straight
        joint move to an IK solution near q_hint / the current posture.  Towards a q_hint, a joint
        swing over BIG_SWING rad is not made unchecked: it is planned (joint_path), or SkillFailure."""
        scene, self.kin.scene = self.kin.scene, None
        try:
            qs, ok = self.kin.cart_path(self.q_cmd, p, R, step=step)
            if ok:
                return qs
            seeds = [np.asarray(q_hint, float)] if q_hint is not None else []
            q_goal, ok = self.kin.ik_global(p, R, seeds=seeds + [self.q_cmd])
        finally:
            self.kin.scene = scene
        if not ok:
            raise SkillFailure(f"no IK for {label or p}")
        if scene is not None and seeds and float(np.max(np.abs(q_goal - self.q_cmd))) > BIG_SWING:
            return self._joint_path(q_goal, label, FREE)[0]
        return self._dense(self.q_cmd, q_goal)

    def _carrying(self, side="right"):
        """An object in the hand (its tilt is held on planned moves)."""
        h = _held_of(self, side)
        return h is not None and h.get("kind") != "bimanual"

    @staticmethod
    def _dense(qa, qb):
        """Straight joint interpolation qa -> qb, about 0.01 rad apart (qa left out)."""
        k = max(2, int(np.max(np.abs(qb - qa)) / 0.01))
        return [qa + (qb - qa) * u for u in np.linspace(0, 1, k)[1:]]

    def joint_path_via(self, vias):
        """Dense joint waypoints from q_cmd through ``vias`` (already checked)."""
        out, qa = [], self.q_cmd.copy()
        for qb in vias:
            out += self._dense(qa, np.asarray(qb, float))
            qa = qb
        return out

    def joint_path(self, q_goal, label=None, allow=FREE):
        """Joint-space move to q_goal: the straight interpolation when it is collision-free (and keeps
        a held object level), else a cuRobo trajectory, else (checked) SkillFailure instead of
        pushing through (the straight interpolation once swept the hand through a cabinet);
        unchecked, the straight interpolation."""
        qs, allow = self._joint_path(np.asarray(q_goal, float), label, allow)
        self.clear.motion(label, allow)
        return qs

    def _joint_path(self, q_goal, label, allow):
        return self._motion_path(label, allow, self.kin, lambda: self._joint_plan(q_goal, label),
                                 lambda: self._dense(self.q_cmd.copy(), q_goal))

    def _joint_plan(self, q_goal, label):
        q0 = self.q_cmd.copy()
        carry = self._carrying()
        if self.kin.segment_free(q0, q_goal) and not (carry and tips_over(self.kin, q0, q_goal)):
            return self._dense(q0, q_goal)
        qs, status = self.kin.plan(q0, q_goal, carry=carry)
        if qs is None:
            raise SkillFailure(f"joint move to {label}: no collision-free trajectory ({status})")
        self.log("joint_plan", target=label, waypoints=len(qs), carry=carry)
        return self.joint_path_via(qs)

    def grip(self, width, steps=100, gradual=False, side="right"):
        """``side``'s gripper to ``width`` (m per finger) over ``steps`` ticks (``gradual``: a smooth ramp)."""
        attr = "grip_cmd" if side == "right" else "left_grip_cmd"
        if getattr(self, "sticky", None) is not None:
            self.sticky.on_open(side, width)      # letting go: the weld goes before the fingers open
        if gradual and steps > 1:
            start = float(getattr(self, attr))
            ramp = max(1, steps // 2)
            for i in range(1, ramp + 1):
                u = i / ramp
                setattr(self, attr, start + (width - start) * (3 * u**2 - 2 * u**3))
                self.step(1)
            setattr(self, attr, width)
            self.step(steps - ramp)
        else:
            setattr(self, attr, width)
            self.step(steps)
        f = _fingers_of(self, side)
        self.log("grip" if side == "right" else "left_grip", cmd=width, fingers=[round(v, 4) for v in f])
        return f

    def left_grip(self, width, steps=100):
        if getattr(self, "sticky", None) is not None:
            self.sticky.on_open("left", width)
        self.left_grip_cmd = float(width)
        self.step(steps)
        f = self.left_fingers()
        self.log("left_grip", cmd=width, fingers=[round(v, 4) for v in f])
        return f

    def left_follow(self, qs, steps_per_wp=3, settle=150, tol=0.02):
        """Drive left arm and shared torso joints through IK waypoints."""
        self.clear.executing()
        vmax = 0.6 * vel_limits(self.left_kin.names)
        for q in qs:
            q = np.asarray(q, float)
            current = np.r_[self.q_cmd[:2], self.left_q_cmd]
            need = int(math.ceil(np.max(np.abs(q-current) / vmax) * PHYSICS_HZ))
            self.q_cmd[:2] = q[:2]
            self.left_q_cmd = q[2:].copy()
            self.step(max(steps_per_wp, need))
        for _ in range(settle):
            if np.max(np.abs(self.left_q()-np.r_[self.q_cmd[:2], self.left_q_cmd])) < tol:
                break
            self.step(2)

    def follow_both(self, right_goal, left_goal, *, label="bimanual", steps=None):
        """Drive both arms at once while checking each sampled paired posture."""
        self.clear.motion(label, FREE, side="both", follows=False)
        self.sync_world()
        self.world.left_active = True
        qr0 = self.q_cmd.copy()
        ql0 = np.r_[self.q_cmd[:2], self.left_q_cmd]
        qr1 = np.asarray(right_goal, float)
        ql1 = np.asarray(left_goal, float)
        if qr1.shape != qr0.shape or ql1.shape != ql0.shape:
            raise ValueError("bimanual joint goals must match both 9-joint chains")
        if np.max(np.abs(qr1[:2]-ql1[:2])) > 0.005:
            raise SkillFailure("bimanual: arms request conflicting torso/waist positions")
        vmax = np.minimum(vel_limits(self.kin.names), vel_limits(self.left_kin.names))
        duration = max(np.max(np.abs(qr1-qr0)/vmax), np.max(np.abs(ql1-ql0)/vmax))/0.5
        n = max(steps or 0, 20, int(math.ceil(duration * PHYSICS_HZ)))
        saved_right, saved_left = self.world.right_q, self.world.left_q
        try:
            for u in np.linspace(0, 1, max(3, n//8)):
                qr = qr0+(qr1-qr0)*u
                ql = ql0+(ql1-ql0)*u
                self.world.right_q, self.world.left_q = qr, ql
                if not self.kin.free(qr) or not self.left_kin.free(ql):
                    raise SkillFailure(f"{label}: paired-arm path collides at {u:.2f}")
        finally:
            self.world.right_q, self.world.left_q = saved_right, saved_left
        for u in np.linspace(0, 1, n)[1:]:
            qr = qr0+(qr1-qr0)*u
            ql = ql0+(ql1-ql0)*u
            self.q_cmd = qr
            self.left_q_cmd = ql[2:].copy()
            self.step(1)
        self.step(90)
        right_error = float(np.max(np.abs(self.q()-qr1)))
        left_error = float(np.max(np.abs(self.left_q()-ql1)))
        self.log("bimanual_follow", target=label, right_q_err=round(right_error, 4),
                 left_q_err=round(left_error, 4))
        if max(right_error, left_error) > 0.06:
            raise SkillFailure(f"{label}: joint tracking error exceeded 0.06 rad")

    def move_left_to(self, p, R, *, label=None, allow=FREE):
        """Collision-checked Cartesian motion for the left fingertip TCP; ``allow`` as in move_to."""
        self.sync_world()
        self.world.left_active = True
        p = np.asarray(p, float)
        if self._exits_contact(allow, self.left_kin):
            if self._leave_contact(label, allow, self.left_kin, lambda: self._left_path(p, R, label, LEGACY),
                                   self.left_follow):
                return self.move_left_to(p, R, label=label, allow=FREE_ELSE_STRAIGHT)
        else:
            qs, allow = self._motion_path(label, allow, self.left_kin, lambda: self._left_path(p, R, label, FREE),
                                          lambda: self._left_path(p, R, label, LEGACY))
            self.clear.motion(label, allow, side="left")
            self.left_follow(qs)
        tcp, _ = self.left_kin.tcp(self.left_q())
        err = float(np.linalg.norm(tcp-p))
        self.log("left_reach", target=label, tcp_err_m=round(err, 4))
        if err > 0.03:
            raise SkillFailure(f"left arm: TCP missed {label or p} by {err:.3f} m")
        return err

    def _left_path(self, p, R, label, allow):
        """move_left_to's waypoints under ``allow`` (FREE or unchecked); SkillFailure when none."""
        collision = allow.checked
        scene = self.left_kin.scene
        if not collision:
            self.left_kin.scene = None
        try:
            start = np.r_[self.q_cmd[:2], self.left_q_cmd]
            qs, ok = self.left_kin.cart_path(start, p, R, step=0.015)
            if not ok:
                goal, ok = self.left_kin.ik_global(p, R, seeds=[start])
                if not ok:
                    raise SkillFailure(f"left arm: no IK for {label or p}")
                if collision and not self.left_kin.segment_free(start, goal):
                    qs, status = self.left_kin.plan(start, goal)
                    if qs is None:
                        raise SkillFailure(f"left arm: no collision-free trajectory for {label or p} ({status})")
                else:
                    n = max(2, int(np.max(np.abs(goal-start))/0.01))
                    qs = [start+(goal-start)*u for u in np.linspace(0, 1, n)[1:]]
        finally:
            self.left_kin.scene = scene
        return qs

    def tuck(self, hang=True):
        """Bring the arm into a travel posture: the fold (rest), else -- where the fold collides at
        this base pose -- hanging at the side (kin.drive, the base planner's detour posture); the
        two are one goal set, the fold preferred, and the one chosen is reached by joint_path
        (straight when that is free, else a cuRobo trajectory).  A place just let go of leaves the
        hand right above the load (3b: no retreat past the contact exit), where the fold may not
        fit (T12 s11: the tray on the bookcase) and a base plan cannot start with the arm
        reaching in.  ``hang`` False: the fold only.  False, the arm left where it is, when there
        is none.  Free space, the fingers in the collision model (_fingers_checked): an open hand
        folded away over a load just let go knocked it over (T04)."""
        self.sync_world()
        with self._fingers_checked(self.kin):
            rest = self.kin.rest
            try:
                goal = next((q for q in ((rest, self.kin.drive) if hang else (rest,)) if self.kin.free(q)), None)
                if goal is None:
                    raise SkillFailure("the rest" + (" and the hanging" if hang else "") + " posture collide here")
                qs = self.joint_path(goal, "tuck")
            except SkillFailure as exc:
                self.log("tuck_blocked", reason=str(exc)[:200],
                         rest_penetration=round(self.kin.penetration(rest), 4),
                         current_penetration=round(self.kin.penetration(self.q_cmd), 4))
                return False
            self.follow(qs)
            return True

    # ------------------------------------------------------------ base
    def set_base(self, x, y, yaw_deg):
        """Holonomic base: drive targets of its x, y and yaw joints for the next tick (velocity:
        the step from the last target, so a pose set every tick is tracked without lag; the yaw
        step the short way round).  The yaw target is kept in (-pi, pi]."""
        yaw = math.radians(yaw_deg)
        dyaw = (yaw - self.base_cmd[2] + math.pi) % (2 * math.pi) - math.pi
        step = np.array([float(x) - self.base_cmd[0], float(y) - self.base_cmd[1], dyaw])
        # capped: a far jump (a start pose set at once) at its one-tick speed would fling the robot
        self.base_vel = np.clip(step / self.sim.get_physics_dt(), -BASE_VMAX, BASE_VMAX)
        self.base_cmd = np.array([float(x), float(y), (yaw + math.pi) % (2 * math.pi) - math.pi])
        self.kin.set_base((x, y, 0.0), yaw)
        self.left_kin.set_base((x, y, 0.0), yaw)

    def swing(self, posture, label, allow=FREE, settle=150, tol=0.01):
        """The body and both arms straight in joint space to ``posture`` (motion_state.Posture) with a
        gentle start and stop: a posture switch the caller checked (the base planner's,
        Motion.base_depths)."""
        self.clear.motion(label, allow, side="both", follows=False)
        r0, l0 = self.q_cmd.copy(), self.left_q_cmd.copy()
        r1, l1 = posture.pair()
        r1, l1 = np.asarray(r1, float), np.asarray(l1, float)[-len(l0):]
        vr = self._vmax()
        vl = np.minimum(0.6 * vel_limits(self.left_kin.names[2:]), vr[2:].max())
        T = max(float(np.max(np.abs(r1 - r0) / vr)), float(np.max(np.abs(l1 - l0) / vl)), 0.05) * 1.5
        n = max(2, int(math.ceil(T * PHYSICS_HZ)))
        for i in range(1, n + 1):
            u = i / n
            u = u * u * (3 - 2 * u)
            self.q_cmd = r0 + (r1 - r0) * u
            self.left_q_cmd = l0 + (l1 - l0) * u
            self.step(1)
        for _ in range(settle):
            if max(np.max(np.abs(self.q() - self.q_cmd)), np.max(np.abs(self.left_q()[2:] - self.left_q_cmd))) < tol:
                break
            self.step(2)
        self.log("swing", target=label, q_err=round(float(np.max(np.abs(self.q() - self.q_cmd))), 4))

    def drive_base(self, path, speed=None, turn=None, ramp=None, on_step=None, allow=BASE_DRIVE):
        """Follow a list of (x, y, yaw_deg) waypoints with one smooth time
        scaling over the whole path (accelerate over ``ramp`` s, cruise,
        decelerate) instead of stopping at every waypoint: the stop-and-go
        jerks shook pinched objects out of the hand.

        ``speed``, ``turn``, ``ramp``: at most the cap of what the hands hold (_drive_cap), the ramp
        at least its least one.  ``allow``: BASE_DRIVE (the arms not checked along the path) unless
        the path is a whole-body plan (base_planner)."""
        self.clear.motion("drive_base", allow, side="base", follows=False)
        cap_v, cap_w, least_ramp = self._drive_cap()
        speed = cap_v if speed is None else min(speed, cap_v)
        turn = cap_w if turn is None else min(turn, cap_w)
        ramp = max(DRIVE_RAMP if ramp is None else ramp, least_ramp)
        x0, y0, yaw0 = self.base_pose()
        # the arm posture this drive carries (actual joints, TCP and lowest joint)
        qa = self.q()
        _, _, J = self.kin.fk_all(qa)
        tcp_a, _ = self.kin.tcp(qa)
        self.log("drive_arm", q=np.round(qa, 3).tolist(), q_cmd=np.round(self.q_cmd, 3).tolist(), tcp=np.round(tcp_a, 3).tolist(),
                 min_joint_z=round(float(min(j[0][2] for j in J[2:])), 3),
                 q_err=round(float(np.max(np.abs(qa - self.q_cmd))), 3))
        pts = [(x0, y0, yaw0)]
        for x, y, yaw in path:
            yaw = pts[-1][2] + (yaw - pts[-1][2] + 180.0) % 360.0 - 180.0     # unwrap
            pts.append((x, y, yaw))
        P = np.array(pts, float)
        # segment "durations" at cruise speed: translation or rotation, whichever is slower
        dur = np.maximum(np.hypot(*np.diff(P[:, :2], axis=0).T) / speed, np.abs(np.radians(np.diff(P[:, 2]))) / turn)
        cum = np.r_[0.0, np.cumsum(dur)]
        T = float(cum[-1])
        if T > 1e-6:
            r = min(ramp, T / 2)
            total = T + r                      # time with trapezoidal ramps
            n = max(20, int(total * PHYSICS_HZ))
            for i in range(1, n + 1):
                t = total * i / n
                if t < r:
                    u = 0.5 * t * t / r
                elif t < total - r:
                    u = t - 0.5 * r
                else:
                    u = T - 0.5 * (total - t) ** 2 / r
                k = min(len(dur) - 1, int(np.searchsorted(cum, u, side="right")) - 1)
                f = 0.0 if dur[k] <= 0 else (u - cum[k]) / dur[k]
                q = P[k] + (P[k + 1] - P[k]) * min(max(f, 0.0), 1.0)
                self.set_base(q[0], q[1], q[2])
                if on_step is not None:
                    on_step(float(u / T), (float(q[0]), float(q[1]), float(q[2])))
                self.step(1)
                if i % HELD_CHECK_EVERY == 0:
                    from .skills import check_held, check_left_held
                    if self.held is not None:
                        check_held(self, "carry")
                    if self.left_held is not None:
                        check_left_held(self, "left_carry")
        self.step(20)
        self.log("base", pose=[round(v, 3) for v in self.base_pose()])

    # ------------------------------------------------------------ video
    @staticmethod
    def _compose(imgs, cap):
        """Main view (+ an inset of a second camera if given) + caption, JPEG-encoded
        (raw frames of a long episode do not fit in memory)."""
        import cv2
        img = np.ascontiguousarray(imgs[0])
        h, w = img.shape[:2]
        if len(imgs) > 1:
            small = cv2.resize(imgs[1], (w // 3, h // 3))
            img[h - h // 3 - 10:h - 10, w - w // 3 - 10:w - 10] = small
        cv2.rectangle(img, (0, 0), (w, 56), (0, 0, 0), -1)
        cv2.putText(img, f"Zeno Malo | {cap}", (16, 38), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        ok, buf = cv2.imencode(".jpg", img[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
        return buf

    def write_video(self, path, fps=None):
        """The frames as an MP4 at real time (a frame every ``stride`` physics ticks) unless ``fps``."""
        import cv2
        import imageio.v2 as imageio
        if not self.frames:
            return None
        w = imageio.get_writer(path, fps=fps or PHYSICS_HZ / self.stride, macro_block_size=1, quality=8)
        for buf in self.frames:
            w.append_data(cv2.imdecode(buf, cv2.IMREAD_COLOR)[..., ::-1])
        w.close()
        return path


