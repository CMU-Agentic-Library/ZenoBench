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


class Dropped(SkillFailure):
    """The held object left the hand while carrying it (worth a re-pick)."""


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
        self.frames = []             # JPEG bytes, composed as they are rendered
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
        self.focus_z = None          # follow-camera target height (low for floor picks)
        from .evaluator import Geometry
        self.geo = Geometry(ann)

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

    def state(self):
        """{"objects": {name: {pos, quat}}, "joints": {art: q}} (evaluator format)."""
        objs = {}
        for name in self.ann.objects:
            p, q = self.obj_pose(name)
            objs[name] = {"pos": p.tolist(), "quat": q.tolist()}
        return {"objects": objs, "joints": {a["name"]: self.joint(a["name"]) for a in self.ann.articulated}}

    def sync_world(self):
        """Planner/IK model <- simulator: joint values of every articulated
        part, the real base pose (planning moves kin's base around) and the
        free objects low enough to block the base column."""
        for a in self.ann.articulated:
            self.world.set_joint(a["name"], self.joint(a["name"]))
        st = self.state()
        boxes = []
        for name in self.ann.objects:
            if self.held is not None and name == self.held["name"]:
                continue
            b = self.geo.bottom(name, st)
            if b[2] > 0.25 and not self._overhangs(name, st):
                continue
            x0, y0, x1, y1 = self.geo.footprint(name, st, margin=0.01)
            boxes.append([x0, y0, b[2], x1, y1, b[2] + self.ann.asset_of(self.ann.objects[name])["size"][2]])
        self.world.set_base_obstacles(boxes)
        x, y, yaw = self.base_pose()
        self.kin.set_base((x, y, 0.0), math.radians(yaw))

    def _overhangs(self, name, st):
        """Object sticking out past its support's edge (pushed for an edge
        pinch): the base column must not drive into it."""
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
                imgs = []
                for cam in self.cams.values():
                    cam.update(1 / 120)
                    imgs.append(cam.data.output["rgb"][0, ..., :3].cpu().numpy())
                self.frames.append(self._compose(imgs, self.caption))

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
                qs = self.joint_path(np.asarray(q_hint, float), label, check=collision)
                ok = True
            if not ok:
                q_goal, ok2 = self.kin.ik_global(np.asarray(p, float), R, seeds=[self.q_cmd])
                if not ok2:
                    raise SkillFailure(f"no IK for {label or p}")
                qs = self.joint_path(q_goal, label, check=collision)
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

    def joint_path(self, q_goal, label=None, check=True):
        """Joint-space move to q_goal, collision-checked (the straight
        interpolation used to sweep the hand through a cabinet): direct, else
        through the tucked posture, else fail instead of pushing through."""
        q0 = self.q_cmd.copy()

        def dense(qa, qb):
            k = max(2, int(np.max(np.abs(qb - qa)) / 0.01))
            return [qa + (qb - qa) * u for u in np.linspace(0, 1, k)[1:]]
        from .planner import _segment_free
        if not check or self.kin.scene is None or _segment_free(self.kin, q0, q_goal):
            return dense(q0, q_goal)
        if not self.kin.free(q0) and self.kin.free(q_goal):
            # starting in contact (hand still at a handle it just released):
            # no collision-free path can start here, leave the contact directly
            self.log("joint_from_contact", target=label)
            return dense(q0, q_goal)
        for via in (self.kin.rest, np.r_[self.kin.rest[:2], q_goal[2:]], np.r_[q_goal[:2], self.kin.rest[2:]]):
            if self.kin.free(via) and _segment_free(self.kin, q0, via) and _segment_free(self.kin, via, q_goal):
                self.log("joint_detour", target=label)
                return dense(q0, via) + dense(via, q_goal)
        raise SkillFailure(f"joint move to {label}: every joint-space path collides")

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

    def drive_base(self, path, speed=0.35, turn=0.8, ramp=0.8):
        """Follow a list of (x, y, yaw_deg) waypoints with one smooth time
        scaling over the whole path (accelerate over ``ramp`` s, cruise,
        decelerate) instead of stopping at every waypoint: the stop-and-go
        jerks shook pinched objects out of the hand."""
        x0, y0, yaw0 = self.base_pose()
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
                self.step(1)
        self.step(20)
        self.log("base", pose=[round(v, 3) for v in self.base_pose()])

    # ------------------------------------------------------------ video
    @staticmethod
    def _compose(imgs, cap):
        """Main view + inset of the second camera + caption, JPEG-encoded
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

    def write_video(self, path, fps=30):
        import cv2
        import imageio.v2 as imageio
        if not self.frames:
            return None
        w = imageio.get_writer(path, fps=fps, macro_block_size=1, quality=8)
        for buf in self.frames:
            w.append_data(cv2.imdecode(buf, cv2.IMREAD_COLOR)[..., ::-1])
        w.close()
        return path
