"""Sticky hands: pick and carry always succeed (profile switch ``execution.sticky_hands``).

An execution assist for planner development under the GT profile, never for the benchmark:
grasping stays physical as long as it works, and the assist only covers what the friction
grasp gets wrong.

* weld: while an object is held (``rig.held`` / ``rig.left_held`` set to a dict) a PhysX fixed
  joint ties it to the gripper link at the relative pose of that moment, so nothing jumps and
  nothing slips out while carrying.  The object stays a dynamic body: collisions still act on
  it (and, through the joint, on the arm).
* release: the joint goes before the fingers open (``rig.grip`` wider than the fingers stand)
  and whenever the hand is cleared (``rig.held = None``).  Place and release stay physical.
* snap: a pick whose physical attempt fails (no park, no IK, not held) still ends with the
  object in the hand.  The robot keeps the motion it managed (or reaches toward the object),
  then the object is set at the planned grasp pose relative to the TCP, the fingers close on it
  and the weld holds it.  ``snap_pick`` is called by the contract runner for ``pick`` only after
  its preconditions held, so precondition and gate failures stay failures.

* caught neighbour: a pick that lifted the container or tray its object stood in or on along with
  it (pinched together) lets go and snaps the object alone, so the weld does not carry the
  container away for good (``after_pick``).
* place: a place whose physical attempt fails (no park, slipped, tipped over, fell off) or leaves
  the object off its receptacle still ends with it there.  The hand lets go and lifts clear, then
  the object is set level (its most vertical axis turned upright: a face-down book stays face
  down) at a free spot on the support (the hint first) or on the container's floor, and settles.
  ``snap_place`` is called by the contract runner for ``place`` only after its preconditions held.

Events (``rig.log``, the worker / rollout log): ``sticky_weld``, ``sticky_release``,
``sticky_snap`` (reason no_park / not_held / ik / caught_neighbour / other), ``sticky_keep``,
``sticky_caught``, ``sticky_place`` / ``sticky_place_retry`` / ``sticky_place_none``.
Planner-facing results do not show them.

Checked in Isaac Sim 5.1 / Isaac Lab 2.3 (CPU physics, dt 1/120): a UsdPhysics.FixedJoint
defined or removed while the simulation runs takes effect on the next step, the articulation
and rigid-body views stay valid, and a tensor-API pose write (SingleRigidPrim) sticks at once.
"""

from __future__ import annotations

import math

import numpy as np

from .evaluator import quat_R
from .physics import ASSET

JOINTS = "/World/StickyHands"
LINKS = {"right": ASSET + "/right_gripper_link", "left": ASSET + "/left_gripper_link"}
NEAR = 0.30            # the hand this close to the object: snap it where the hand is
SHUT = 0.003           # fingers closer than this hold nothing between the pads


def _wxyz(R):
    from scipy.spatial.transform import Rotation
    x, y, z, w = Rotation.from_matrix(R).as_quat()
    return np.array([w, x, y, z])


def note_grasp(rig, name, p, R, kind="pinch", pre_open=0.04):
    """A physical pick goes for TCP pose (p, R) on ``name``: the snap reuses that grasp."""
    s = getattr(rig, "sticky", None)
    if s is not None:
        pos, quat = rig.obj_pose(name)
        s.plans[name] = {"p": np.array(p, float), "R": np.array(R, float), "pos": pos, "quat": quat,
                         "kind": kind, "pre_open": float(pre_open)}


def welded(rig, hand, name=None):
    s = getattr(rig, "sticky", None)
    return s is not None and s.welded(hand, name)


def snap_pick(rig, name, exc):
    """Contract-runner hook for a pick whose policy failed: True when ``name`` ends up held."""
    s = getattr(rig, "sticky", None)
    if s is None or name not in rig.ann.objects:
        return False
    if rig.held is not None:
        if rig.held.get("name") != name:
            return False
        rig.log("sticky_keep", obj=name, error=str(exc)[:200])      # held already, a later leg failed
        return True
    return s.snap(name, failure_reason(str(exc)), str(exc))


def snap_place(rig, name, receptacle, hint, before, error):
    """Contract-runner hook for a place whose policy failed or left ``name`` off ``receptacle``:
    True when it ends up resting on / in it (StickyHands.place)."""
    s = getattr(rig, "sticky", None)
    if s is None or name not in rig.ann.objects:
        return False
    return s.place(name, receptacle, hint, before, str(error))


def rest_R(quat):
    """The orientation levelled: the body axis nearest the vertical turned onto it (upright stays
    upright, a face-down book stays face down, yaw is kept)."""
    R0 = quat_R(quat)
    i = int(np.argmax(np.abs(R0[2])))
    a = R0[:, i] * np.sign(R0[2, i])
    ax = np.cross(a, [0.0, 0.0, 1.0])
    sn = float(np.linalg.norm(ax))
    if sn < 1e-9:
        return R0
    from scipy.spatial.transform import Rotation
    return Rotation.from_rotvec(ax / sn * math.atan2(sn, float(a[2]))).as_matrix() @ R0


def after_pick(rig, name, before):
    """Contract-runner hook after a pick that succeeded: see StickyHands.drop_caught."""
    s = getattr(rig, "sticky", None)
    if s is not None and rig.held is not None and rig.held.get("name") == name:
        s.drop_caught(name, before)


def caught_neighbours(rig, name, before, st):
    """Objects the pick lifted along that stood at or below the picked one (the container or tray
    it was in or on, pinched together with it) and are near the hand.  What stood on or in the
    picked object (a lid, the contents) is its load, not caught."""
    tcp, _ = rig.kin.tcp(rig.q())
    z0 = before["bottoms"][name][2]
    out = []
    for o, b in before["bottoms"].items():
        if o == name or o not in st["objects"] or b[2] > z0 + 0.01:
            continue
        dz = float(rig.geo.bottom(o, st)[2]) - b[2]
        if dz > 0.02 and float(np.linalg.norm(np.asarray(rig.geo.centre(o, st), float) - tcp)) < 0.35:
            out.append((o, round(dz, 3)))
    return out


def failure_reason(msg):
    m = msg.lower()
    if any(k in m for k in ("not held", "not grasped", "lift/contact", "did not move with", "slipped",
                            "contact pose missed")):
        return "not_held"
    if any(k in m for k in ("no ik", "ik changed", "not solvable", "every joint-space path")):
        return "ik"
    if any(k in m for k in ("base pose", "reachable grasp", "base path", "park", "unreachable", "overhang")):
        return "no_park"
    return "other"


class StickyHands:
    def __init__(self, rig):
        self.rig = rig
        self.welds = {}            # hand -> object name
        self.plans = {}            # object -> the grasp the last physical pick went for
        self._links = {}

    # ------------------------------------------------------------ weld
    def link_pose(self, hand):
        """Gripper link pose as PhysX has it (identical to the arm FK of the measured joints)."""
        prim = self._links.get(hand)
        if prim is None:
            from isaacsim.core.prims import SingleRigidPrim
            prim = SingleRigidPrim(LINKS[hand], name=f"sticky_{hand}_gripper_link")
            prim.initialize()
            self._links[hand] = prim
        p, q = prim.get_world_pose()
        return p.cpu().numpy().astype(float), quat_R(q.cpu().numpy().astype(float))

    def welded(self, hand, name=None):
        w = self.welds.get(hand)
        return w is not None and (name is None or w == name)

    def _add_joint(self, hand, body, rel_p, rel_R):
        from pxr import Gf, UsdPhysics
        j = UsdPhysics.FixedJoint.Define(self.rig.stage, f"{JOINTS}/{hand}")
        j.CreateBody0Rel().SetTargets([LINKS[hand]])
        j.CreateBody1Rel().SetTargets([body])
        j.CreateLocalPos0Attr().Set(Gf.Vec3f(*(float(v) for v in rel_p)))
        j.CreateLocalRot0Attr().Set(Gf.Quatf(*(float(v) for v in _wxyz(rel_R))))
        j.CreateLocalPos1Attr().Set(Gf.Vec3f(0.0, 0.0, 0.0))
        j.CreateLocalRot1Attr().Set(Gf.Quatf(1.0, 0.0, 0.0, 0.0))
        j.CreateExcludeFromArticulationAttr().Set(True)      # a loose constraint, not an articulation joint

    def _remove_joint(self, hand):
        self.rig.stage.RemovePrim(f"{JOINTS}/{hand}")

    def weld(self, hand, name, why):
        """Fixed joint gripper link -> object body at their current relative pose."""
        if self.welds.get(hand) == name:
            return
        if self.welds.get(hand) is not None:
            self.release(hand, "new_grasp")
        if name in self.welds.values():          # two-handed hold: one weld (to the first hand) is enough
            return
        rig = self.rig
        lp, lR = self.link_pose(hand)
        op, oq = rig.obj_pose(name)
        self._add_joint(hand, rig.ann.objects[name]["body"], lR.T @ (op - lp), lR.T @ quat_R(oq))
        self.welds[hand] = name
        rig.log("sticky_weld", hand=hand, obj=name, why=why, link_to_body_m=round(float(np.linalg.norm(op - lp)), 4))

    def release(self, hand, why):
        name = self.welds.pop(hand, None)
        if name is None:
            return None
        rig = self.rig
        self._remove_joint(hand)
        rig.log("sticky_release", hand=hand, obj=name, why=why)
        # a handover: the other hand closed on the same object keeps it welded
        other = "left" if hand == "right" else "right"
        h = rig.left_held if other == "left" else rig.held
        cmd = rig.left_grip_cmd if other == "left" else rig.grip_cmd
        if h is not None and h.get("name") == name and float(cmd) < 0.01:
            self.weld(other, name, "handover")
        return name

    # ------------------------------------------------------------ rig hooks
    def on_hold(self, hand, value):
        """``rig.held`` (right) / ``rig.left_held`` is about to become ``value``."""
        name = value.get("name") if isinstance(value, dict) else None
        if name is None:
            self.release(hand, "hand_cleared")
        elif name in self.rig.ann.objects:
            self.weld(hand, name, "grasp")

    def on_open(self, hand, width):
        """``rig.grip`` / ``rig.left_grip`` to ``width``: wider than the fingers stand is letting go."""
        if self.welds.get(hand) is None:
            return
        f = self.rig.fingers() if hand == "right" else self.rig.left_fingers()
        if float(width) > float(np.max(f)) + 0.001:
            self.release(hand, "fingers_open")

    def close(self):
        """Episode end: no joint outlives it."""
        for hand in list(self.welds):
            self.release(hand, "episode_end")

    def drop_caught(self, name, before):
        """A pinch that also caught what the object stood in (an apple pinched against its
        basket's wall) would, once welded, carry that along for good: a physical grasp slips
        off it sooner or later.  Let go, lift the open hand clear, snap the object alone."""
        from .rig import SkillFailure
        rig = self.rig
        caught = caught_neighbours(rig, name, before, rig.state())
        if not caught:
            return False
        rig.log("sticky_caught", obj=name, caught=caught)
        rig.grip(0.04, 40)                               # the weld goes first (fingers open)
        rig.held = None
        tcp, R = rig.kin.tcp(rig.q_cmd)
        for up in (0.15, 0.10, 0.06):
            try:
                rig.move_to(tcp + np.array([0, 0, up]), R, step=0.005, label="sticky_clear", collision=False)
                break
            except SkillFailure:
                continue
        rig.step(60)                                     # the neighbour settles back
        return self.snap(name, "caught_neighbour", "pinch also lifted " + ", ".join(o for o, _ in caught))

    # ------------------------------------------------------------ snap
    def _grasp(self, name):
        """Object pose in the TCP frame for the grasp to snap into, with its held kind and opening.
        The physical attempt's own grasp first, then an annotated pinch, an edge pinch for flat
        objects, the object centred between the pads last."""
        rig = self.rig
        pos, quat = rig.obj_pose(name)
        Rb = quat_R(quat)
        plan = self.plans.get(name)
        if plan is not None:
            return dict(rel_p=plan["R"].T @ (plan["pos"] - plan["p"]),
                        rel_R=plan["R"].T @ quat_R(plan["quat"]), kind=plan["kind"],
                        pre_open=plan["pre_open"], source="planned")
        obj = rig.ann.objects[name]
        asset = rig.ann.asset_of(obj)
        bx, by, _ = rig.base_pose()
        try:
            cands = rig.ann.grasp_poses(obj, pos, quat)
        except Exception:
            cands = []
        if cands:
            g = min(cands, key=lambda c: float(np.linalg.norm(c["p"][:2] - np.array([bx, by]))) +
                    0.3 * c.get("along_rank", 0))
            return dict(rel_p=g["R"].T @ (pos - g["p"]), rel_R=g["R"].T @ Rb, kind="pinch",
                        pre_open=float(g["pre_open"]), source=f"annotated_{g['kind']}")
        size = np.asarray(asset["size"], float)
        from .kinematics import gripper_rot
        if size[2] < 0.06 and max(size[:2]) > 0.07:
            # flat: an edge pinch on the side facing the robot (as _edge_pinch_impl)
            from .skills import EDGE_GRIP_DEPTH, _half_along, _yaw
            b = np.asarray(rig.geo.bottom(name, rig.state()), float)
            n = np.array([bx, by]) - b[:2]
            n = n / max(1e-9, float(np.linalg.norm(n)))
            h = _half_along(size, _yaw(quat), n)
            tcp = np.r_[b[:2] + n * (h - EDGE_GRIP_DEPTH), b[2] + size[2] / 2]
            R = gripper_rot(-np.r_[n, 0.0], [0, 0, 1.0])
            return dict(rel_p=R.T @ (pos - tcp), rel_R=R.T @ Rb, kind="edge",
                        pre_open=min(0.04, float(size[2]) / 2 + 0.012), source="edge_default")
        R = gripper_rot([0, 0, -1.0], [1.0, 0.0, 0.0])
        c = np.asarray(rig.geo.centre(name, rig.state()), float)
        return dict(rel_p=R.T @ (pos - c), rel_R=R.T @ Rb, kind="pinch", pre_open=0.04, source="centred")

    def _reach(self, name, grasp):
        """Bring the hand to the object as far as the arm allows: the grasp's pre-pose, else a
        pose in front of the body.  Nothing to do when the hand is there already (a failed grasp
        or lift)."""
        from .rig import SkillFailure
        rig = self.rig
        tcp, _ = rig.kin.tcp(rig.q())
        pos, quat = rig.obj_pose(name)
        if float(np.linalg.norm(tcp - pos)) < NEAR:
            return "at_object"
        R_g = quat_R(quat) @ grasp["rel_R"].T                   # the grasp on the object where it is now
        p_g = pos - R_g @ grasp["rel_p"]
        appr = -R_g[:, 2]
        rig.sync_world()
        rig.kin.coll_kw = {"ignore_fingers": True}
        for label, p in (("sticky_reach_pre", p_g - 0.08 * appr + np.array([0, 0, 0.04])),
                         ("sticky_reach_above", p_g + np.array([0, 0, 0.12]))):
            try:
                rig.move_to(p, R_g, step=0.01, label=label)
                return label
            except SkillFailure:
                continue
        x, y, yaw = rig.base_pose()
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        for lx, ly, z in ((0.35, -0.10, 0.9), (0.40, -0.25, 1.0), (0.35, -0.10, 0.75)):
            for R in (R_g, rig.kin.tcp(rig.q_cmd)[1]):
                try:
                    rig.move_to(np.array([x + c * lx - s * ly, y + s * lx + c * ly, z]), R, step=0.01,
                                label="sticky_reach_front")
                    return "front"
                except SkillFailure:
                    continue
        return "none"

    def snap(self, name, reason, error):
        rig = self.rig
        grasp = self._grasp(name)
        reach = self._reach(name, grasp)
        before, _ = rig.obj_pose(name)
        rig.grip(grasp["pre_open"], 30)                 # an open hand (nothing is welded yet)
        tcp, R = rig.kin.tcp(rig.q())
        body, Rb = tcp + R @ grasp["rel_p"], R @ grasp["rel_R"]
        t = rig.torch
        b = rig._bodies[name]
        b.set_world_pose(t.tensor(body, dtype=t.float32), t.tensor(_wxyz(Rb), dtype=t.float32))
        b.set_linear_velocity(t.zeros(3))
        b.set_angular_velocity(t.zeros(3))
        self.weld("right", name, "snap")                 # same tick: the object never falls
        f = rig.grip(0.0, 60, gradual=True)
        if float(np.min(f)) < SHUT:
            # nothing between the pads (a grasp guessed for an object with no annotated pinch):
            # keep them just apart, the weld holds the object (not rig.grip: opening releases it)
            rig.grip_cmd = 0.01
            rig.step(20)
            f = rig.fingers()
        tcp, R = rig.kin.tcp(rig.q())
        body, quat = rig.obj_pose(name)
        held = {"name": name, "kind": grasp["kind"], "tcp_minus_body": tcp - body, "R": R,
                "pre_open": grasp["pre_open"]}
        st = rig.state()
        if grasp["kind"] == "corner":
            from .skills import _lowest_z
            held["body_minus_low"] = float(body[2] - _lowest_z(rig, name, st))
        elif grasp["kind"] == "edge":
            from .skills import _half_along, _perp, _yaw
            size = rig.ann.asset_of(rig.ann.objects[name])["size"]
            n = R[:2, 2] / max(1e-9, float(np.linalg.norm(R[:2, 2])))       # fingers point along -n
            b = np.asarray(rig.geo.bottom(name, st), float)
            h = _half_along(size, _yaw(quat), n)
            held.update(h=h, depth=float(h - n @ (tcp[:2] - b[:2])), lat_half=_half_along(size, _yaw(quat), _perp(n)),
                        dz=float(tcp[2] - b[2]))
        rig.held = held
        rig.log("sticky_snap", obj=name, reason=reason, error=error[:200], grasp=grasp["source"],
                kind=grasp["kind"], reach=reach, moved_m=round(float(np.linalg.norm(body - before)), 3),
                fingers=np.round(f, 4).tolist())
        return True

    # ------------------------------------------------------------ place
    def _place_centres(self, name, receptacle, hint, half_h):
        """Box centres for the object (``half_h`` from its lowest point to its centre) on / in the
        receptacle, best first: free spots on a support (free_spots: the hint when it is free), or
        a container's floor, then just over its rim (dropped in)."""
        rig = self.rig
        if receptacle in rig.ann.objects:
            st = rig.state()
            cb = np.asarray(rig.geo.bottom(receptacle, st), float)
            c = np.asarray(rig.geo.centre(receptacle, st), float)
            rim = float(rig.ann.asset_of(rig.ann.objects[receptacle])["container"]["rim_height"])
            return [np.r_[c[:2], cb[2] + 0.015 + half_h], np.r_[c[:2], cb[2] + rim + 0.02 + half_h]]
        from .skills import free_spots
        z = float(rig.ann.support(receptacle)["z"]) + 0.005 + half_h
        return [np.r_[float(x), float(y), z] for x, y in free_spots(rig, name, receptacle, hint)]

    def place(self, name, receptacle, hint, before, error):
        """Set ``name`` down on / in ``receptacle``: the targets are found first (nothing found, the
        object stays as it is), then the hand lets go (the weld goes first) and lifts clear, the
        object is set level at a target the hand is not over and settles; the next target when it
        does not end up there (fell off, toppled)."""
        from .rig import SkillFailure
        rig = self.rig
        obj0 = (before or {}).get("objects", {}).get(name) or {}
        # the orientation the place started with (still in the hand), not where a failed release left it
        R = rest_R(obj0["quat"] if obj0.get("quat") is not None else rig.obj_pose(name)[1])
        a = rig.ann.asset_of(rig.ann.objects[name])
        size = np.asarray(a["size"], float)
        c_b = np.asarray(a["origin_to_bottom_center"], float) + np.array([0.0, 0.0, size[2] / 2])
        half_h = float(np.abs(R[2]) @ size) / 2
        try:
            centres = self._place_centres(name, receptacle, hint, half_h)
        except Exception as e:                           # an unannotated receptacle: nothing to snap to
            rig.log("sticky_place_none", obj=name, receptacle=receptacle, error=str(e)[:200])
            return False
        if not centres:
            rig.log("sticky_place_none", obj=name, receptacle=receptacle, error="no free spot")
            return False
        if rig.held is not None and rig.held.get("name") == name:
            rig.grip(0.04, 40)
            rig.held = None
            tcp, Rt = rig.kin.tcp(rig.q_cmd)
            for up in (0.10, 0.05):
                try:
                    rig.move_to(tcp + np.array([0, 0, up]), Rt, step=0.005, label="sticky_clear", collision=False)
                    break
                except SkillFailure:
                    continue
        # spots under the hand last (it stays where the attempt left it)
        tcp, _ = rig.kin.tcp(rig.q())
        reach = 0.5 * float(np.hypot(size[0], size[1])) + 0.08
        centres.sort(key=lambda c: float(np.linalg.norm(c[:2] - tcp[:2])) < reach and tcp[2] < c[2] + half_h + 0.08)
        t = rig.torch
        b = rig._bodies[name]
        q = t.tensor(_wxyz(R), dtype=t.float32)
        container = receptacle in rig.ann.objects
        for i, c in enumerate(centres[:4]):
            b.set_world_pose(t.tensor(c - R @ c_b, dtype=t.float32), q)
            b.set_linear_velocity(t.zeros(3))
            b.set_angular_velocity(t.zeros(3))
            rig.step(60)
            st = rig.state()
            ok, why = (rig.geo.inside if container else rig.geo.on)(name, receptacle, st)
            cos = (float(np.trace(R.T @ quat_R(st["objects"][name]["quat"]))) - 1.0) / 2
            turned = math.degrees(math.acos(max(-1.0, min(1.0, cos))))
            if ok and turned < 20:
                rig.log("sticky_place", obj=name, receptacle=receptacle, error=error[:200], spot=i,
                        centre=np.round(c, 3).tolist(), turned_deg=round(turned, 1))
                return True
            rig.log("sticky_place_retry", obj=name, receptacle=receptacle, spot=i, detail=str(why),
                    turned_deg=round(turned, 1))
        return False
