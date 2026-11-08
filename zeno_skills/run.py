"""Executing a plan (docs/MOTION_ARCHITECTURE.md section 8).  So far: ``observe``, the State of
the simulated robot and world as the planner sees them."""

from __future__ import annotations

import numpy as np

from .kinematics import FINGER_OPEN
from .motion_state import Hand, Held, State


def observe(rig):
    """The State now: the base, the commanded arm postures, the head, each hand's finger opening
    (the wider finger, as Motion.live_locks) and what it holds (its box frame in the TCP frame,
    Motion.held_in_tcp), the objects' box frames and the parts' joint values, all as synced into
    the collision model (Rig.sync_world)."""
    rig.sync_world()
    motion = rig.kin.motion
    hands = {}
    for side, kin, q, held, fingers in (
            ("right", rig.kin, rig.q_cmd, rig.held, rig.fingers),
            ("left", rig.left_kin, np.r_[rig.q_cmd[:2], rig.left_q_cmd], rig.left_held, rig.left_fingers)):
        width = float(np.clip(np.asarray(fingers(), float)[:2].max(), 0.0, FINGER_OPEN))
        h = None
        if held is not None:
            name = held["name"]
            T = motion.held_in_tcp(kin, q, name) if motion is not None and motion.by_owner.get(f"object:{name}") \
                else np.eye(4)
            h = Held(name, T, held.get("kind", "pinch"))
        hands[side] = Hand(width=width, held=h)
    return State(base=tuple(rig.base_pose()), q_right=np.asarray(rig.q_cmd, float).copy(),
                 q_left=np.asarray(rig.left_q_cmd, float).copy(), head=dict(rig.head_q()), hands=hands,
                 objects=motion.object_frames() if motion is not None else {},
                 parts={a["name"]: rig.joint(a["name"]) for a in rig.ann.articulated})
