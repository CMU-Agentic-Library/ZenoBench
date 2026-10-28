"""Zeno Malo arm kinematics around the *fingertip* TCP (not the wrist flange).

Forward kinematics and the Jacobian are exact numpy from the URDF chain.  Every
inverse query (``ik``, ``ik_global``, ``cart_path``) and every collision check
(``free``) goes to cuRobo (motion.py, ``kin.motion``) against the scene's real
PhysX colliders; ``kin.scene = None`` makes a query kinematic-only (self
collision still counts).  Without a Motion (offline tools, unit tests) there is
no IK.

The old skills targeted ``right_gripper_link`` directly, whose origin is the wrist
mount; the fingers point along the link's -Z and their pads sit ~0.09-0.14 m below
it.  Everything here is expressed for a TCP at the pad centre so GT object/handle
poses can be used without hand-tuned offsets.
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[1]
URDF = ROOT / "robot_sources/zeno_malo_description-master/zeno_malo_edu.isaac.urdf"
FRAME = "right_gripper_link"
FINGERS = ("right_gripper_left_finger_axis", "right_gripper_right_finger_axis")
FINGER_OPEN = 0.04          # m per finger (8 cm max gap)
# compact right-arm fold (hand 0.29 m to the side, 0.33 m ahead), not used
COMPACT_TUCK = [0.0, 0.0, 1.05, 0.46, 0.42, 2.04, -0.06, -0.26, 0.42]

# default left-arm travel posture; Rig can command all seven left joints
LEFT_ARM_FOLD = {"left_arm_joint_1": 0.2, "left_arm_joint_2": 0.35, "left_arm_joint_4": 2.3}
# right_gripper_link origin -> pad centre along the link's -Z (finger joints at
# -0.12985, pads span -0.14..-0.09 on the finger links).
TCP_DEPTH = 0.12
CARRY_TILT = 0.15           # rad: largest tilt of a held object from its start orientation on a planned move


def gripper_rot(approach, close_dir):
    """World rotation of right_gripper_link: fingers point along ``approach``
    (= -Z_link) and close along ``close_dir`` (= Y_link)."""
    z = -np.asarray(approach, float)
    z /= np.linalg.norm(z)
    y = np.asarray(close_dir, float)
    y = y - z * (y @ z)
    y /= np.linalg.norm(y)
    x = np.cross(y, z)
    return np.column_stack((x, y, z))


def tilt(Ra, Rb):
    """Angle between the world z axis carried by Ra and by Rb (rotation about z is not tilt)."""
    z = (np.asarray(Rb) @ np.asarray(Ra).T)[:, 2]
    return float(np.arccos(np.clip(z[2], -1.0, 1.0)))


def max_tilt(kin, R0, qs):
    """Largest tilt from R0 of the TCP along the joint waypoints qs."""
    return max((tilt(R0, kin.tcp(q)[1]) for q in qs), default=0.0)


def manipulability(kin, q):
    """Yoshikawa manipulability of the arm joints at q (sqrt det J J^T; torso and waist left out)."""
    J = kin.jac(np.asarray(q, float))[0][:, 2:]
    return float(np.sqrt(max(np.linalg.det(J @ J.T), 0.0)))


def yaw_quat_wxyz(yaw):
    return np.array([math.cos(yaw / 2), 0.0, 0.0, math.sin(yaw / 2)])


def effort_limits(names):
    joints = {j.get("name"): j for j in ET.parse(URDF).getroot().findall("joint")}
    return np.array([float(joints[n].find("limit").get("effort")) for n in names])


def vel_limits(names):
    joints = {j.get("name"): j for j in ET.parse(URDF).getroot().findall("joint")}
    return np.array([float(joints[n].find("limit").get("velocity")) for n in names])


def _limits(names):
    joints = {j.get("name"): j for j in ET.parse(URDF).getroot().findall("joint")}
    lo, hi = [], []
    for n in names:
        lim = joints[n].find("limit")
        lo.append(float(lim.get("lower")) + 1e-4)
        hi.append(float(lim.get("upper")) - 1e-4)
    return np.array(lo), np.array(hi)


def _chain(side="right"):
    """base_link -> selected gripper link joints (all URDF rpy are zero)."""
    if side not in ("right", "left"):
        raise ValueError(f"unknown arm side: {side}")
    root = ET.parse(URDF).getroot()
    by_child = {j.find("child").get("link"): j for j in root.findall("joint")}
    out, link = [], f"{side}_gripper_link"
    while link in by_child:
        j = by_child[link]
        xyz = np.array([float(v) for v in j.find("origin").get("xyz").split()])
        ax = j.find("axis")
        axis = np.array([float(v) for v in ax.get("xyz").split()]) if ax is not None else None
        out.append((j.get("name"), j.get("type"), xyz, axis, link))
        link = j.find("parent").get("link")
    return out[::-1]


def _axis_rot(axis, a):
    """Rodrigues for a unit axis (hot path: no scipy)."""
    x, y, z = axis
    c, s = math.cos(a), math.sin(a)
    C = 1.0 - c
    return np.array([[c + x * x * C, x * y * C - z * s, x * z * C + y * s],
                     [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
                     [z * x * C - y * s, z * y * C + x * s, c + z * z * C]])


def _cross(a, b):
    return np.array([a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]])


class ArmKin:
    def __init__(self, side="right"):
        self.side = side
        chain = _chain(side)
        self.children = [c[4] for c in chain]
        self.chain = [c[:4] for c in chain]
        self.names = [c[0] for c in self.chain if c[1] != "fixed"]
        self.lo, self.hi = _limits(self.names)
        # stay off the hard limits: the joint drives stall a few hundredths
        # short of them (a solution at the limit was a 6 cm TCP error)
        # (arm joints only: floor picks need the torso and waist at their limits)
        m = np.r_[0.0, 0.0, np.full(len(self.names) - 2, 0.03)]
        self.lo, self.hi = self.lo + m, self.hi - m
        # A relaxed, elbow-out posture used as a null-space attractor.
        posture = ([0.0, 0.0, 0.3, 1.2, 0.0, 1.3, 0.0, 0.0, 0.0] if side == "right" else
                   [0.0, 0.0, 0.2, 0.35, 0.0, 2.3, 0.0, 0.0, 0.0])
        self.posture = np.clip(np.array(posture), self.lo, self.hi)
        # Travel (tucked) posture = the same elbow-out posture.  (A compact fold
        # close to the chest was tried: it put every pick on another IK branch
        # and the fridge/cabinet/left-arm motions regressed; COMPACT_TUCK keeps
        # it for reference.)
        self.rest = self.posture.copy()
        self.base_p, self.base_R = np.zeros(3), np.eye(3)

    def set_base(self, xyz, yaw):
        self.base_p = np.asarray(xyz, float)
        self.base_R = Rotation.from_euler("z", yaw).as_matrix()

    def fk_all(self, q):
        """Link pose plus per-joint world (origin, axis, type) for the Jacobian."""
        p, R = self.base_p.copy(), self.base_R.copy()
        joints, i = [], 0
        for name, typ, xyz, axis in self.chain:
            p = p + R @ xyz
            if typ == "fixed":
                continue
            w = R @ axis
            joints.append((p.copy(), w, typ))
            if typ == "prismatic":
                p = p + w * q[i]
            else:
                R = R @ _axis_rot(axis, q[i])
            i += 1
        return p, R, joints

    def fk(self, q):
        p, R, _ = self.fk_all(np.asarray(q, float))
        return p, R

    def tcp(self, q):
        p, R = self.fk(q)
        return p - TCP_DEPTH * R[:, 2], R

    def jac(self, q):
        p, R, joints = self.fk_all(q)
        tcp = p - TCP_DEPTH * R[:, 2]
        J = np.zeros((6, len(joints)))
        for i, (o, w, typ) in enumerate(joints):
            if typ == "prismatic":
                J[:3, i] = w
            else:
                J[:3, i] = _cross(w, tcp - o)
                J[3:, i] = w
        return J, tcp, R

    scene = None          # the WorldModel (base navigation; carries the other arm's joints); None: no collision
    motion = None         # motion.Motion (cuRobo); set by runtime.make_rig
    coll_kw = {}

    def _motion(self):
        if self.motion is None:
            raise RuntimeError("no cuRobo motion backend on this ArmKin (runtime.make_rig sets kin.motion)")
        return self.motion

    def _other_q(self):
        sc = self.scene
        if sc is None:
            return None
        return getattr(sc, "left_q" if self.side == "right" else "right_q", None)

    def ik(self, p_t, R_t, q0, **_):
        """IK seeded with q0 (stays on q0's branch), kinematic only."""
        return self._motion().ik(self, np.asarray(p_t, float), R_t, [np.asarray(q0, float)], False,
                                 self._other_q(), self.coll_kw, local=True)

    def free(self, q):
        if self.scene is None:
            return True
        return self._motion().free(self, q, self._other_q(), self.coll_kw)

    def segment_free(self, qa, qb):
        if self.scene is None:
            return True
        return self._motion().segment_free(self, qa, qb, self._other_q(), self.coll_kw)

    def ik_global(self, p_t, R_t, seeds=None):
        """cuRobo's multi-seed IK (collision-aware unless scene is None); seeds first."""
        seeds = list(seeds or []) + [self.posture]
        return self._motion().ik(self, np.asarray(p_t, float), R_t, seeds, self.scene is not None,
                                 self._other_q(), self.coll_kw)

    def cart_path(self, q0, p_goal, R_goal, step=0.01):
        """Straight-line TCP path (slerp orientation) as a joint-space waypoint list."""
        return self._motion().cart_path(self, np.asarray(q0, float), np.asarray(p_goal, float), R_goal, step,
                                        self.scene is not None, self._other_q(), self.coll_kw)

    def plan(self, q0, q1, carry=False):
        """cuRobo joint-space trajectory q0 -> q1 (collision-free), or (None, status); ``carry``
        holds the tilt of an object in the hand."""
        return self._motion().plan(self, q0, q1, self._other_q(), self.coll_kw, carry=carry)

    def plan_to(self, q0, p_goal, R_goal, carry=False):
        """Constrained trajectory for a blocked Cartesian leg (Motion.plan_to)."""
        return self._motion().plan_to(self, np.asarray(q0, float), self.tcp(q0)[0], np.asarray(p_goal, float),
                                      R_goal, self._other_q(), self.coll_kw, carry=carry)

    def clearance(self, Q, targets=()):
        """Per row of Q: the arm's distance to the world (m, capped; Motion.clearance)."""
        if self.scene is None:
            return np.full(len(np.atleast_2d(Q)), np.inf)
        return self._motion().clearance(self, Q, targets, self._other_q(), self.coll_kw)

    def penetration(self, q):
        """Deepest penetration of the arm into the world at q (m, >= 0)."""
        return self._motion().penetration(self, q, self._other_q(), self.coll_kw)
