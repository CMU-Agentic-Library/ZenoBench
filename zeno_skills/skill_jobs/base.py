"""The whole-body base model on a rig (motion_state.BaseModel, docs/MOTION_ARCHITECTURE.md 2.5, 5.4)."""

from __future__ import annotations

import math
import numpy as np

from ..rig import SkillFailure
from ..skills import (_base_plan, _reachable)


class RigBase:
    """motion_state.BaseModel on a rig: the whole-body base planner (base_planner over
    Motion.body_spheres / base_depths), what the hands hold riding as they sit in them now."""

    def __init__(self, rig):
        self.rig = rig

    def plan(self, state, goal, chain, label, quiet=False):
        try:
            steps, used = _base_plan(self.rig, goal, chain, label, state=state, quiet=quiet)
        except SkillFailure as exc:
            return None, str(exc)
        out = []
        for st in steps:
            if st.kind == "drive":
                out.append(("drive", [tuple(float(v) for v in w) for w in st.path[1:]], used[st.mode][0]))
            else:
                name, (qr, ql) = used[st.mode + 1]
                out.append(("swing", name, np.asarray(qr, float), np.asarray(ql, float)))
        return out, None

    def straight(self, state, target, label):
        return _straight_base_check(self.rig, state, target, label)

    def depths(self, state, poses):
        from ..skill_plans import travel_chain
        rig = self.rig
        motion = rig.kin.motion
        if motion is None or not len(poses):
            return [0.0] * len(poses)
        posture = travel_chain(rig.kin, rig.left_kin, state)[0][1]
        return list(motion.base_depths(rig, np.array([[x, y, math.radians(yaw)] for x, y, yaw in poses]),
                                       motion.body_spheres(rig, [posture]))[0])

    def reachable(self, state, poses):
        return _reachable(self.rig.world, state.base, poses)

    def drivable(self, state, goal):
        from ..planner import plan_path
        from ..skill_plans import travel_chain
        rig = self.rig
        if rig.kin.motion is None:
            return plan_path(rig.world, tuple(state.base), goal) is not None
        return self.plan(state, goal, travel_chain(rig.kin, rig.left_kin, state), "drivable", quiet=True)[0] is not None


def _straight_base_check(rig, state, target, label):
    """RigBase.straight: ([target, the yaw the short way round], None), or (None, why)."""
    from .. import base_planner
    motion = rig.kin.motion
    x, y, yaw = state.base
    tx, ty, tyaw = target
    tyaw = yaw + (tyaw - yaw + 180.0) % 360.0 - 180.0
    if motion is not None:
        sph = motion.body_spheres(rig, [(state.q_right, state.q_left)])
        poses = base_planner.segment((x, y, math.radians(yaw)), (tx, ty, math.radians(tyaw)),
                                     float(np.max(np.hypot(sph[0][:, 0], sph[0][:, 1]))))
        us = np.linspace(0, 1, len(poses))
        d = motion.base_depths(rig, poses, sph)[0]
        low = rig.world.footprints_clear(poses)
        bad = (d > d[0] + base_planner.DEPTH_TOL) | ~low
        bad[0] = False
        if bad.any():
            k = int(np.argmax(bad))
            return None, (f"{label}: blocked {us[k] * 100:.0f}% of the way (" +
                          (f"{d[k] * 1000:.0f} mm into the world)" if d[k] > d[0] + base_planner.DEPTH_TOL
                           else "base footprint)"))
    return [(float(tx), float(ty), float(tyaw))], None
