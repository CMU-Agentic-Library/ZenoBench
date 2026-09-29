"""Zeno Malo right-arm kinematics around the *fingertip* TCP (not the wrist flange).

Pure numpy (exact FK from the URDF chain, analytic Jacobian, damped least
squares IK with a null-space posture term).  An optional collision checker
(``kin.scene``, see collision.py) makes ``ik_global``/``cart_path`` return only
collision-free configurations.

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
# left arm is held folded so it never hangs into the floor/furniture
LEFT_ARM_FOLD = {"left_arm_joint_1": 0.2, "left_arm_joint_2": 0.35, "left_arm_joint_4": 2.3}
# right_gripper_link origin -> pad centre along the link's -Z (finger joints at
# -0.12985, pads span -0.14..-0.09 on the finger links).
TCP_DEPTH = 0.12


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


def rot_to_wxyz(R):
    xyzw = Rotation.from_matrix(R).as_quat()
    return np.r_[xyzw[3], xyzw[:3]]


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


def _chain():
    """base_link -> right_gripper_link joints (all URDF rpy are zero)."""
    root = ET.parse(URDF).getroot()
    by_child = {j.find("child").get("link"): j for j in root.findall("joint")}
    out, link = [], "right_gripper_link"
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


def _rotvec(R):
    """log map of a rotation matrix (hot path: no scipy)."""
    c = max(-1.0, min(1.0, (R[0, 0] + R[1, 1] + R[2, 2] - 1.0) / 2.0))
    th = math.acos(c)
    v = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])
    if th < 1e-6:
        return 0.5 * v
    if th > math.pi - 1e-4:
        return Rotation.from_matrix(R).as_rotvec()
    return th / (2 * math.sin(th)) * v


class ArmKin:
    def __init__(self, solver=None):
        self.solver = solver
        chain = _chain()
        self.children = [c[4] for c in chain]
        self.chain = [c[:4] for c in chain]
        self.names = [c[0] for c in self.chain if c[1] != "fixed"]
        if solver is not None:
            assert list(solver.get_joint_names()) == self.names, solver.get_joint_names()
        self.lo, self.hi = _limits(self.names)
        # stay off the hard limits: the joint drives stall a few hundredths
        # short of them (a solution at the limit was a 6 cm TCP error)
        # (arm joints only: floor picks need the torso and waist at their limits)
        m = np.r_[0.0, 0.0, np.full(len(self.names) - 2, 0.03)]
        self.lo, self.hi = self.lo + m, self.hi - m
        # A relaxed, elbow-out posture used as a null-space attractor.
        self.rest = np.clip(np.array([0.0, 0.0, 0.3, 1.2, 0.0, 1.3, 0.0, 0.0, 0.0]),
                            self.lo, self.hi)
        self.base_p, self.base_R = np.zeros(3), np.eye(3)

    def set_base(self, xyz, yaw):
        self.base_p = np.asarray(xyz, float)
        self.base_R = Rotation.from_euler("z", yaw).as_matrix()
        if self.solver is not None:
            self.solver.set_robot_base_pose(self.base_p, yaw_quat_wxyz(yaw))

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

    def _err(self, q, p_t, R_t, w_rot):
        p, R = self.tcp(q)
        e_rot = Rotation.from_matrix(R_t @ R.T).as_rotvec()
        return np.r_[p_t - p, w_rot * e_rot]

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

    def ik(self, p_t, R_t, q0, iters=150, w_rot=0.35, tol_p=0.004, tol_r=0.04):
        """Damped least squares on the TCP pose (analytic Jacobian)."""
        q = np.clip(np.asarray(q0, float).copy(), self.lo, self.hi)
        W = np.diag([1, 1, 1, w_rot, w_rot, w_rot])
        for it in range(iters + 80):
            polish = it >= iters            # final phase: no null-space pull, light damping
            J, p, R = self.jac(q)
            e = np.r_[p_t - p, _rotvec(R_t @ R.T)]
            ep = np.linalg.norm(e[:3])
            if ep < tol_p and np.linalg.norm(e[3:]) < tol_r:
                return q, True
            if it == 60 and ep > 0.08:          # hopeless seed: give up early
                return q, False
            Jw, ew = W @ J, W @ e
            JJt = Jw @ Jw.T + (0.002 if polish else 0.01) * np.eye(6)
            step = Jw.T @ np.linalg.solve(JJt, ew)
            if not polish:
                N = np.eye(len(q)) - Jw.T @ np.linalg.solve(JJt, Jw)
                step += 0.05 * N @ (self.rest - q)
            n = np.linalg.norm(step)
            if n > 0.2:
                step *= 0.2 / n
            q = np.clip(q + step, self.lo, self.hi)
        p, R = self.tcp(q)
        e = np.r_[p_t - p, Rotation.from_matrix(R_t @ R.T).as_rotvec()]
        return q, bool(np.linalg.norm(e[:3]) < tol_p * 2 and np.linalg.norm(e[3:]) < tol_r * 2)

    scene = None          # optional Scene; when set, IK results must be collision-free
    margin = 0.005
    coll_kw = {}

    def free(self, q):
        return self.scene is None or self.scene.clearance(self, q, **self.coll_kw) > self.margin

    def ik_global(self, p_t, R_t, seeds=None):
        """Try several seeds and return the first collision-free solution."""
        cands = list(seeds or []) + [self.rest]
        rng = np.random.default_rng(0)
        cands += [rng.uniform(self.lo, self.hi) for _ in range(14)]
        for c in cands:
            q, ok = self.ik(p_t, R_t, c)
            if ok and self.free(q):
                return q, True
        return q, False

    def cart_path(self, q0, p_goal, R_goal, step=0.01):
        """Straight-line TCP path (slerp orientation) as a joint-space waypoint list."""
        p0, R0 = self.tcp(q0)
        n = max(2, int(np.ceil(np.linalg.norm(p_goal - p0) / step)) + 1)
        ang = np.linalg.norm(Rotation.from_matrix(R_goal @ R0.T).as_rotvec())
        n = max(n, int(np.ceil(ang / 0.05)) + 1)
        from scipy.spatial.transform import Slerp
        slerp = Slerp([0, 1], Rotation.from_matrix([R0, R_goal]))
        out, q = [], np.asarray(q0, float)
        for u in np.linspace(0, 1, n)[1:]:
            q, ok = self.ik(p0 + (p_goal - p0) * u, slerp(u).as_matrix(), q)
            if not ok or not self.free(q):
                return out, False
            out.append(q.copy())
        return out, True
