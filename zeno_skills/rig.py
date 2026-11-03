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
from .kinematics import ArmKin, FINGERS, LEFT_ARM_FOLD, tips_over, vel_limits, yaw_quat_wxyz
from .physics import ASSET, BASE_JOINTS

BIG_SWING = 1.0           # rad: an unchecked joint move swinging further is planned (a 2 rad swing put the forearm through a trash can)
CARRY_VEL = 0.5           # rad/s: arm joint speed cap with an object in the hand (it must not be flung)
RIM_VEL = 0.25            # rad/s: ...with a container hanging from a one-hand rim pinch (it pivots in the pads)
LEAVE_GAP = 0.005         # m: closer to the world than this, the robot (and its load) still touches it
LEAVE_MARGIN = 0.01       # m: a contact exit runs this far past where the robot (and its load) first comes clear
LEAVE_MAX = 0.06          # m: ...and no further; still touching there, the rest is the logged straight fallback


class SkillFailure(RuntimeError):
    pass


class Dropped(SkillFailure):
    """The held object left the hand while carrying it (worth a re-pick)."""


BASE_VMAX = np.array([1.0, 1.0, 2.0])     # m/s, m/s, rad/s: base velocity targets beyond are clipped


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
        self.grip_cmd = 0.04
        self.tick, self.stride = 0, stride
        self.frames = []             # JPEG bytes, composed as they are rendered
        self.events, self.caption, self.trace = [], "", []
        self.clear = Clearance(self)        # collision policy of the motions + contact monitor (clearance.py)
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
            self._bodies[name] = b
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
        ev = {"tick": self.tick, "t": round(self.tick / 120, 3), "label": label, **kw}
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
            self.robot.apply_action(ArticulationAction(joint_positions=t.tensor(self.q_cmd, dtype=t.float32),
                                                       joint_indices=self.arm))
            self.robot.apply_action(ArticulationAction(joint_positions=t.full((2,), float(self.grip_cmd)),
                                                       joint_indices=self.fing))
            self.robot.apply_action(ArticulationAction(joint_positions=t.tensor(self.left_q_cmd, dtype=t.float32),
                                                       joint_indices=self.left))
            self.robot.apply_action(ArticulationAction(joint_positions=t.full((2,), float(self.left_grip_cmd)),
                                                       joint_indices=self.left_fing))
            self.robot.apply_action(ArticulationAction(joint_positions=t.tensor(self.head_cmd, dtype=t.float32),
                                                       joint_indices=self.head))
            # the yaw target within half a turn of the joint's reading, the reading kept in
            # [-pi, pi): PhysX refuses targets of the unlimited yaw joint (eREVOLUTE) beyond
            # +-2 pi, which left the base turned away from where the planner put it, but lets the
            # reading itself run on.  A reading past pi is set back by a turn (the same pose).
            base_q = self.base_cmd.copy()
            yaw = float(self.robot.get_joint_positions()[self.base.long()][2])
            if abs(yaw) > math.pi:
                yaw = (yaw + math.pi) % (2 * math.pi) - math.pi
                self.robot.set_joint_positions(t.tensor([yaw], dtype=t.float32), joint_indices=self.base[2:])
            base_q[2] = yaw + (base_q[2] - yaw + math.pi) % (2 * math.pi) - math.pi
            self.robot.apply_action(ArticulationAction(joint_positions=t.tensor(base_q, dtype=t.float32),
                                                       joint_velocities=t.tensor(self.base_vel, dtype=t.float32),
                                                       joint_indices=self.base))
            self.base_vel = np.zeros(3)         # a set_base each tick keeps the base moving
            render = bool(self.cams) and self.tick % self.stride == 0
            self.sim.step(render=render)
            self.tick += 1
            if self.tick % 12 == 0:
                self._advance_thermal(0.1)
            if self.clear.monitor and self.tick % MONITOR_EVERY == 0:
                self.clear.tick()
            if render:
                imgs = []
                for cam in self.cams.values():
                    cam.update(1 / 120)
                    imgs.append(cam.data.output["rgb"][0, ..., :3].cpu().numpy())
                self.frames.append(self._compose(imgs, self.caption))

    def _held_container(self):
        """The right hand holds a container (by its rim: it hangs off a thin wall)."""
        h = self.held
        if h is None or h.get("kind") == "bimanual" or h.get("name") not in self.ann.objects:
            return False
        return bool(self.ann.asset_of(self.ann.objects[h["name"]]).get("container"))

    def _vmax(self):
        """Joint speeds paths are executed at: 60% of the URDF limits (torso lift is 0.117 m/s;
        ignoring this was a 0.29 m tracking error); with an object in the hand the arm joints at
        most CARRY_VEL (RIM_VEL for a rim-held container) so it is not flung."""
        v = 0.6 * vel_limits(self.kin.names)
        if self._carrying():
            v[2:] = np.minimum(v[2:], RIM_VEL if self._held_container() else CARRY_VEL)
        return v

    def follow_smooth(self, qs, steps_per_wp=3, settle=150, tol=0.01):
        """Follow the same planned joint waypoints with a gentle start and stop.

        Time scaling only changes progress along the existing joint segments;
        it never rounds a corner into a configuration outside that path.
        """
        points = [self.q_cmd.copy()] + [np.asarray(q, float) for q in qs]
        if len(points) == 1:
            return
        vmax = self._vmax()
        segment_times = [max(steps_per_wp / 120,
                             float(np.max(np.abs(b - a) / vmax)))
                         for a, b in zip(points[:-1], points[1:])]
        times = np.r_[0.0, np.cumsum(segment_times)]
        path_time = float(times[-1])
        ramp = min(0.8, path_time / 2)
        duration = path_time + ramp
        ticks = max(2, int(math.ceil(duration * 120)))
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
            self.q_cmd = points[segment] + fraction * (points[segment + 1] - points[segment])
            self.step(1)
        for _ in range(settle):
            if np.max(np.abs(self.q() - self.q_cmd)) < tol:
                break
            self.step(2)

    def follow(self, qs, steps_per_wp=3, settle=150, tol=0.01):
        """Waypoints time-scaled to the joint speeds of _vmax; with an object in the hand always
        follow_smooth's gentle start and stop (a jerk shakes it out of the pinch)."""
        if self._carrying():
            return self.follow_smooth(qs, steps_per_wp, settle, tol)
        vmax = self._vmax()
        for q in qs:
            need = int(math.ceil(np.max(np.abs(q - self.q_cmd) / vmax) * 120))
            self.q_cmd = q
            self.step(max(steps_per_wp, need))
        for _ in range(settle):
            if np.max(np.abs(self.q() - self.q_cmd)) < tol:
                break
            self.step(2)

    # ------------------------------------------------------------ arm motions
    # Every arm motion has two ways (docs/COLLISION_PLAN.md principle 2): collision-checked, the
    # straight move when it is free, else a planned trajectory; unchecked, the straight move.
    # A checked motion with a fallback Allow that finds no path makes the unchecked one, logged.
    def move_to(self, p, R, step=0.01, steps_per_wp=3, label=None, allow=FREE, q_hint=None,
                smooth=False):
        """Move the TCP to (p, R): the straight line, else a planned trajectory (_move_path).
        ``q_hint``: a joint solution of the target (find_park's), the planner's joint goal.
        ``allow`` (clearance.Allow): what the move may touch (_motion_path)."""
        self.sync_world()
        p = np.asarray(p, float)
        follow = lambda qs: (self.follow_smooth if smooth else self.follow)(qs, steps_per_wp)
        if self._exits_contact(allow, self.kin):
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

    def move_to_any(self, goals, step=0.01, steps_per_wp=3, label=None, allow=FREE, smooth=False, cost=None):
        """Move the TCP to the goal of the set ``goals`` [(p, R)] the arm gets to most cheaply: one
        batched IK of all of them (collision-free solutions near the current posture, the held
        object in the collision model: Kinematics.ik_set), the reachable goal of least joint
        travel plus ``cost[i]`` (rad), then move_to it with its solution as the joint goal.  The
        goals are not tried one after another: the choice is made before the arm moves, and
        what happens after it is that one motion's (SkillFailure, or ``allow``'s fallback).
        Returns the chosen index; SkillFailure when no goal has a solution."""
        if not goals:
            raise SkillFailure(f"{label}: empty goal set")
        self.sync_world()
        cost = np.zeros(len(goals)) if cost is None else np.asarray(cost, float)
        with self._planning(self.kin, self.q_cmd):
            qs = self.kin.ik_set(goals, self.q_cmd)
        score = np.array([np.inf if q is None else float(np.max(np.abs(q - self.q_cmd))) + c
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
            hit = next((kin.explain(q) for q in list(qs[::5]) + list(qs[-1:]) if not kin.free(q)), None)
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

    def _leave_contact(self, label, allow, kin, straight, follow):
        """The contact segment of a from_contact motion: its straight waypoints only up to
        LEAVE_MARGIN past where the arm, its hand and what the hand holds first come LEAVE_GAP clear
        of the world (none when they start that clear), at most LEAVE_MAX of TCP travel; run under the
        from_contact Allow.  True when the target is still ahead: the caller moves on to it from
        here as a free-space motion (planned; still touching at LEAVE_MAX, the logged straight)."""
        start = self._start(kin)
        qs = straight()
        with self._planning(kin, start, keep_held=True):
            n, clear = self._exit_length(kin, start, qs)
        allow = self._from_contact(kin, allow)
        p0, p1 = kin.tcp(start)[0], kin.tcp(qs[n - 1] if n else start)[0]
        self.log("leave_contact_exit", target=label, exit_m=round(float(np.linalg.norm(p1 - p0)), 4),
                 waypoints=n, of=len(qs), clear=clear)
        if n:
            self.clear.motion(label, allow)
            follow(qs[:n])
        return n < len(qs)

    @staticmethod
    def _exit_length(kin, start, qs):
        """(how many of the straight waypoints ``qs`` the contact segment takes, whether it ends
        clear): up to LEAVE_MARGIN of TCP travel past the first clear one -- clear all along that
        margin -- or up to LEAVE_MAX, or all of them."""
        if not kin.near(start, LEAVE_GAP):
            return 0, True
        p0 = kin.tcp(start)[0]
        since = None                       # TCP travel where the current clear stretch began
        for i, q in enumerate(qs):
            d = float(np.linalg.norm(kin.tcp(q)[0] - p0))
            if d > LEAVE_MAX:
                return i, False
            if kin.near(q, LEAVE_GAP):
                since = None
                continue
            since = d if since is None else since
            if d - since >= LEAVE_MARGIN:
                return i + 1, True
        return len(qs), since is not None

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
            return qs
        carry = self._carrying()
        qs, how = self.kin.plan_to(self.q_cmd, p, R, carry=carry, q_goal=self._goal(p, R, q_hint))
        if qs is None:
            raise SkillFailure(f"no collision-free path to {label or p}: {how}")
        self.log("planned_leg", target=label, how=how, waypoints=len(qs), carry=carry)
        return self.joint_path_via(qs)

    def _goal(self, p, R, q_hint):
        """Joint goal for a planned leg to (p, R): ``q_hint`` re-solved at the actual base on its
        branch, else a collision-free IK solution near q_hint / the current posture, else q_hint
        itself (solved where find_park put the base); None when there is none."""
        seeds = [np.asarray(q_hint, float)] if q_hint is not None else []
        if seeds:
            q, ok = self.kin.ik(p, R, seeds[0])
            if ok and self.kin.free(q):
                return q
        q, ok = self.kin.ik_global(p, R, seeds=seeds + [self.q_cmd])
        if ok:
            return q
        return seeds[0] if seeds and self.kin.free(seeds[0]) else None

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

    def _carrying(self):
        """An object in the right hand (its tilt is held on planned moves)."""
        return self.held is not None and self.held.get("kind") != "bimanual"

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

    def grip(self, width, steps=100, gradual=False):
        if getattr(self, "sticky", None) is not None:
            self.sticky.on_open("right", width)      # letting go: the weld goes before the fingers open
        if gradual and steps > 1:
            start = float(self.grip_cmd)
            ramp = max(1, steps // 2)
            for i in range(1, ramp + 1):
                u = i / ramp
                self.grip_cmd = start + (width - start) * (3 * u**2 - 2 * u**3)
                self.step(1)
            self.grip_cmd = width
            self.step(steps - ramp)
        else:
            self.grip_cmd = width
            self.step(steps)
        f = self.fingers()
        self.log("grip", cmd=width, fingers=[round(v, 4) for v in f])
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
        vmax = 0.6 * vel_limits(self.left_kin.names)
        for q in qs:
            q = np.asarray(q, float)
            current = np.r_[self.q_cmd[:2], self.left_q_cmd]
            need = int(math.ceil(np.max(np.abs(q-current) / vmax) * 120))
            self.q_cmd[:2] = q[:2]
            self.left_q_cmd = q[2:].copy()
            self.step(max(steps_per_wp, need))
        for _ in range(settle):
            if np.max(np.abs(self.left_q()-np.r_[self.q_cmd[:2], self.left_q_cmd])) < tol:
                break
            self.step(2)

    def follow_both(self, right_goal, left_goal, *, label="bimanual", steps=None):
        """Drive both arms at once while checking each sampled paired posture."""
        self.clear.motion(label, FREE)
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
        n = max(steps or 0, 20, int(math.ceil(duration*120)))
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
            self.clear.motion(label, allow)
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

    def tuck(self):
        """Fold the arm to the rest posture: joint_path (straight when that is free, else a cuRobo
        trajectory).  False, the arm left where it is, when there is none."""
        self.sync_world()
        kw = self.kin.coll_kw
        self.kin.coll_kw = {"ignore_fingers": True}
        try:
            rest = self.kin.rest
            try:
                if not self.kin.free(rest):
                    raise SkillFailure("the rest posture collides here")
                qs = self.joint_path(rest, "tuck")
            except SkillFailure as exc:
                self.log("tuck_blocked", reason=str(exc)[:200],
                         rest_penetration=round(self.kin.penetration(rest), 4),
                         current_penetration=round(self.kin.penetration(self.q_cmd), 4))
                return False
            self.follow(qs)
            return True
        finally:
            self.kin.coll_kw = kw

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

    def swing(self, q_right, q_left, label, allow=FREE, settle=150, tol=0.01):
        """Both arms (and the shared torso and waist) straight in joint space to (q_right: torso,
        waist, 7 right-arm joints; q_left: 7 left-arm joints) with a gentle start and stop: a
        posture switch the caller checked (the base planner's, Motion.base_depths)."""
        self.clear.motion(label, allow)
        r0, l0 = self.q_cmd.copy(), self.left_q_cmd.copy()
        r1, l1 = np.asarray(q_right, float), np.asarray(q_left, float)[-len(l0):]
        vr = self._vmax()
        vl = np.minimum(0.6 * vel_limits(self.left_kin.names[2:]), vr[2:].max())
        T = max(float(np.max(np.abs(r1 - r0) / vr)), float(np.max(np.abs(l1 - l0) / vl)), 0.05) * 1.5
        n = max(2, int(math.ceil(T * 120)))
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

    def drive_base(self, path, speed=0.35, turn=0.8, ramp=0.8, on_step=None, allow=BASE_DRIVE):
        """Follow a list of (x, y, yaw_deg) waypoints with one smooth time
        scaling over the whole path (accelerate over ``ramp`` s, cruise,
        decelerate) instead of stopping at every waypoint: the stop-and-go
        jerks shook pinched objects out of the hand.

        A container held by a one-hand rim pinch hangs off a thin wall and
        pivots under base accelerations: it is driven at half speed with a
        longer ramp.  ``allow``: BASE_DRIVE (the arms not checked along the path) unless the path
        is a whole-body plan (base_planner)."""
        self.clear.motion("drive_base", allow)
        if self._held_container():
            speed, turn, ramp = min(speed, 0.18), min(turn, 0.35), max(ramp, 1.8)
        if getattr(self, "left_held", None) is not None and self.held is None:
            # a load in the left hand alone (after a handover) hangs from one
            # pinch: drive gently (a full-speed drive shook a rolling pin out)
            speed, turn, ramp = min(speed, 0.18), min(turn, 0.35), max(ramp, 1.8)
        x0, y0, yaw0 = self.base_pose()
        # the arm posture this drive carries (actual joints, TCP and lowest joint)
        qa = self.q()
        _, _, J = self.kin.fk_all(qa)
        tcp_a, _ = self.kin.tcp(qa)
        self.log("drive_arm", q=np.round(qa, 3).tolist(), tcp=np.round(tcp_a, 3).tolist(),
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
            n = max(20, int(total * 120))
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
                if i % 60 == 0:
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
        """The frames as an MP4 at real time (a frame every ``stride`` ticks of 120 Hz) unless ``fps``."""
        import cv2
        import imageio.v2 as imageio
        if not self.frames:
            return None
        w = imageio.get_writer(path, fps=fps or 120 / self.stride, macro_block_size=1, quality=8)
        for buf in self.frames:
            w.append_data(cv2.imdecode(buf, cv2.IMREAD_COLOR)[..., ::-1])
        w.close()
        return path
