"""Isaac Sim runtime for Zeno Malo: joint-drive control, holonomic base,
state readout and recording.  Only robot drive targets and the base anchor are
ever written; objects and furniture move only through contact.
"""

from __future__ import annotations

import json
import math

import numpy as np

from .kinematics import FINGERS, LEFT_ARM_FOLD, vel_limits, yaw_quat_wxyz
from .physics import ANCHOR, ASSET


class SkillFailure(RuntimeError):
    pass


class Rig:
    def __init__(self, sim, stage, robot, kin, world, ann, cams=None, stride=4, log=print):
        import torch
        from isaacsim.core.prims import SingleArticulation, SingleRigidPrim
        self.torch = torch
        self.sim, self.stage, self.robot, self.kin, self.world, self.ann = sim, stage, robot, kin, world, ann
        self.cams = cams or {}
        self.arm = torch.tensor([robot.dof_names.index(n) for n in kin.names], dtype=torch.int32)
        self.fing = torch.tensor([robot.dof_names.index(n) for n in FINGERS], dtype=torch.int32)
        self.left = torch.tensor([robot.dof_names.index(n) for n in LEFT_ARM_FOLD], dtype=torch.int32)
        self.left_q = torch.tensor(list(LEFT_ARM_FOLD.values()), dtype=torch.float32)
        self.anchor = stage.GetPrimAtPath(ANCHOR)
        self.base_z = float(self.anchor.GetAttribute("physics:localPos0").Get()[2])
        self.q_cmd = self.q()
        self.grip_cmd = 0.04
        self.tick, self.stride = 0, stride
        self.frames = {k: [] for k in self.cams}
        self.events, self.caption, self.trace = [], "", []
        self._log = log
        self._arts, self._bodies = {}, {}
        for a in ann.articulated:
            art = SingleArticulation(a["prim"], name=f"art_{a['name']}")
            art.initialize()
            self._arts[a["name"]] = art
        for name, o in ann.objects.items():
            b = SingleRigidPrim(o["body"], name=f"obj_{name}")
            b.initialize()
            self._bodies[name] = b
        x, y, yaw = self.base_pose()
        self.kin.set_base((x, y, 0.0), math.radians(yaw))
        self.held = None

    # ------------------------------------------------------------ state
    def q(self):
        return self.robot.get_joint_positions()[self.arm.long()].cpu().numpy().astype(float)

    def fingers(self):
        return self.robot.get_joint_positions()[self.fing.long()].cpu().numpy().astype(float)

    def joint(self, art_name):
        return float(self._arts[art_name].get_joint_positions()[0])

    def obj_pose(self, name):
        p, q = self._bodies[name].get_world_pose()
        return p.cpu().numpy().astype(float), q.cpu().numpy().astype(float)

    def base_pose(self):
        p, q = self.robot.get_world_pose()
        p = p.cpu().numpy().astype(float)
        return p[0], p[1], math.degrees(2 * math.atan2(float(q[3]), float(q[0])))

    def sync_world(self):
        """Planner/IK model <- simulator: joint values of every articulated
        part and the real base pose (planning moves kin's base around)."""
        for a in self.ann.articulated:
            self.world.set_joint(a["name"], self.joint(a["name"]))
        x, y, yaw = self.base_pose()
        self.kin.set_base((x, y, 0.0), math.radians(yaw))

    def log(self, label, **kw):
        ev = {"tick": self.tick, "t": round(self.tick / 120, 3), "label": label, **kw}
        self.events.append(ev)
        self._log("EVENT " + json.dumps(ev, default=float))

    # ------------------------------------------------------------ stepping
    def step(self, n=1):
        from isaacsim.core.utils.types import ArticulationAction
        t = self.torch
        for _ in range(n):
            self.robot.apply_action(ArticulationAction(joint_positions=t.tensor(self.q_cmd, dtype=t.float32),
                                                       joint_indices=self.arm))
            self.robot.apply_action(ArticulationAction(joint_positions=t.full((2,), float(self.grip_cmd)),
                                                       joint_indices=self.fing))
            self.robot.apply_action(ArticulationAction(joint_positions=self.left_q, joint_indices=self.left))
            render = bool(self.cams) and self.tick % self.stride == 0
            self.sim.step(render=render)
            self.tick += 1
            if render:
                for k, cam in self.cams.items():
                    cam.update(1 / 120)
                    self.frames[k].append((cam.data.output["rgb"][0, ..., :3].cpu().numpy().copy(), self.caption))

    def follow(self, qs, steps_per_wp=3, settle=150, tol=0.01):
        """Waypoints time-scaled to 60% of URDF velocity limits (torso lift is
        0.117 m/s; ignoring this was a 0.29 m tracking error)."""
        vmax = 0.6 * vel_limits(self.kin.names)
        for q in qs:
            need = int(math.ceil(np.max(np.abs(q - self.q_cmd) / vmax) * 120))
            self.q_cmd = q
            self.step(max(steps_per_wp, need))
        for _ in range(settle):
            if np.max(np.abs(self.q() - self.q_cmd)) < tol:
                break
            self.step(2)

    def move_to(self, p, R, step=0.01, steps_per_wp=3, label=None, collision=True, q_hint=None):
        """Straight TCP line; falls back to the planner-validated step, then to a
        joint-space move to ``q_hint`` (a planner-validated solution)."""
        self.sync_world()
        scene = self.kin.scene
        if not collision:
            self.kin.scene = None
        try:
            qs, ok = self.kin.cart_path(self.q_cmd, np.asarray(p, float), R, step=step)
            if not ok and step < 0.02:
                qs, ok = self.kin.cart_path(self.q_cmd, np.asarray(p, float), R, step=0.02)
                if ok:        # densify for smooth tracking
                    dense = []
                    prev = self.q_cmd
                    for q in qs:
                        k = max(1, int(np.max(np.abs(q - prev)) / 0.01))
                        dense += [prev + (q - prev) * u for u in np.linspace(0, 1, k + 1)[1:]]
                        prev = q
                    qs = dense
            if not ok and q_hint is not None:
                q_goal, ok2 = np.asarray(q_hint, float), True
                n = max(2, int(np.max(np.abs(q_goal - self.q_cmd)) / 0.01))
                qs = [self.q_cmd + (q_goal - self.q_cmd) * u for u in np.linspace(0, 1, n)[1:]]
                ok = True
            if not ok:
                q_goal, ok2 = self.kin.ik_global(np.asarray(p, float), R, seeds=[self.q_cmd])
                if not ok2:
                    raise SkillFailure(f"no IK for {label or p}")
                n = max(2, int(np.max(np.abs(q_goal - self.q_cmd)) / 0.01))
                qs = [self.q_cmd + (q_goal - self.q_cmd) * u for u in np.linspace(0, 1, n)[1:]]
        finally:
            self.kin.scene = scene
        self.follow(qs, steps_per_wp)
        tcp, _ = self.kin.tcp(self.q())
        err = float(np.linalg.norm(tcp - p))
        qe = self.q() - self.q_cmd
        extra = {}
        if np.max(np.abs(qe)) > 0.05:
            extra = {"q": np.round(self.q(), 3).tolist(), "q_cmd": np.round(self.q_cmd, 3).tolist()}
        self.log("reach", target=label, tcp_err_m=round(err, 4), q_err=round(float(np.max(np.abs(qe))), 4), **extra)
        return err

    def grip(self, width, steps=100):
        self.grip_cmd = width
        self.step(steps)
        f = self.fingers()
        self.log("grip", cmd=width, fingers=[round(v, 4) for v in f])
        return f

    def tuck(self):
        """Fold the arm to the rest posture without sweeping through furniture
        or an open door: try (direct | up | back+up) Cartesian retreats, then a
        joint-space fold, every waypoint collision-checked."""
        self.sync_world()
        tcp, R = self.kin.tcp(self.q_cmd)
        back = R[:, 2] * 0.15                       # -approach direction
        kw = self.kin.coll_kw
        self.kin.coll_kw = {"ignore_fingers": True}
        try:
            for pre in ([], [tcp + np.array([0, 0, 0.15])], [tcp + back, tcp + back + np.array([0, 0, 0.25])],
                        [tcp + np.array([0, 0, 0.30])]):
                qs, q, ok = [], self.q_cmd, True
                for p in pre:
                    seg, ok = self.kin.cart_path(q, p, R, 0.02)
                    if not ok:
                        break
                    qs += seg
                    q = seg[-1]
                if not ok:
                    continue
                for target in (self.kin.rest, np.zeros_like(self.kin.rest)):
                    if not self.kin.free(target):
                        continue
                    n = max(2, int(np.max(np.abs(target - q)) / 0.01))
                    fold = [q + (target - q) * u for u in np.linspace(0, 1, n)[1:]]
                    if all(self.kin.free(f) for f in fold[::3]):
                        self.follow(qs + fold)
                        return True
            self.log("tuck_blocked")
            return False
        finally:
            self.kin.coll_kw = kw

    # ------------------------------------------------------------ base
    def set_base(self, x, y, yaw_deg):
        """Holonomic base: move the anchor joint frame; PhysX drags the base."""
        from pxr import Gf
        yaw = math.radians(yaw_deg)
        self.anchor.GetAttribute("physics:localPos0").Set(Gf.Vec3f(float(x), float(y), self.base_z))
        self.anchor.GetAttribute("physics:localRot0").Set(Gf.Quatf(math.cos(yaw / 2), 0.0, 0.0, math.sin(yaw / 2)))
        self.kin.set_base((x, y, 0.0), yaw)

    def drive_base(self, path, speed=0.35, turn=0.8):
        """Follow a list of (x, y, yaw_deg) waypoints."""
        for x, y, yaw_deg in path:
            x0, y0, yaw0 = self.base_pose()
            dyaw = (yaw_deg - yaw0 + 180.0) % 360.0 - 180.0
            n = max(20, int(max(math.hypot(x - x0, y - y0) / speed, abs(math.radians(dyaw)) / turn) * 120))
            for i in range(1, n + 1):
                u = 0.5 - 0.5 * math.cos(math.pi * i / n)
                self.set_base(x0 + (x - x0) * u, y0 + (y - y0) * u, yaw0 + dyaw * u)
                self.step(1)
        self.step(20)
        self.log("base", pose=[round(v, 3) for v in self.base_pose()])

    # ------------------------------------------------------------ video
    def write_video(self, path, fps=30):
        import cv2
        import imageio.v2 as imageio
        keys = list(self.frames)
        if not keys or not self.frames[keys[0]]:
            return None
        out = []
        for i, (img, cap) in enumerate(self.frames[keys[0]]):
            img = np.ascontiguousarray(img)
            h, w = img.shape[:2]
            if len(keys) > 1:
                small = cv2.resize(self.frames[keys[1]][i][0], (w // 3, h // 3))
                img[h - h // 3 - 10:h - 10, w - w // 3 - 10:w - 10] = small
            cv2.rectangle(img, (0, 0), (w, 56), (0, 0, 0), -1)
            cv2.putText(img, f"Zeno Malo | {cap}", (16, 38), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            out.append(img)
        imageio.mimsave(path, out, fps=fps, macro_block_size=1, quality=8)
        return path
