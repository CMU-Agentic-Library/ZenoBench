"""A held tool's working point (docs/motion/MOTION_ARCHITECTURE.md 6, contact skills): the one place a named
``tool_frame`` of an asset's annotation (annotations/assets.json, tools/prepare_assets.TOOL_FRAMES -- the
spoon's "bowl" and "handle" ends) becomes the matrix the plans take, T_tcp_tool = Held.T_tcp_obj . T_obj_tool (4.1).  The
contact skills never convert from the annotation themselves: a new tool is a new annotation."""

from __future__ import annotations

import numpy as np

from ..evaluator import quat_R
from ..rig import SkillFailure


def free_end(rig, state, name, frames):
    """The one of ``frames`` (names of the object's annotated tool frames) farthest from the TCP in the hold
    the State has: the end of a tool not in the hand (a spoon pinched at its bowl stirs with its handle)."""
    return max(frames, key=lambda f: float(np.linalg.norm(tool_in_tcp(rig, state, name, f)[:3, 3])))


def tool_in_tcp(rig, state, name, frame):
    """T_tcp_tool (4x4) of the ``frame`` of the object ``name`` the right hand holds in ``state``: its
    annotated point (in the asset's body frame, identity rotation) through the hold the State has.
    Held.T_tcp_obj is the load's box frame (the collision model's frame of its first collider, where
    State.objects puts it); the annotation is in the body frame the simulator reports (rig.obj_pose):
    the two related as they stand now.  SkillFailure: not held, or no such frame annotated."""
    held = state.held(rig.kin.side)
    if held is None or held.name != name:
        raise SkillFailure(f"{name} is not in the {rig.kin.side} hand")
    frames = rig.ann.asset_of(rig.ann.objects[name]).get("tool_frame") or {}
    if frame not in frames:
        raise SkillFailure(f"{name}: no tool frame {frame!r} annotated (has {sorted(frames)})")
    # the box frame where the hold puts it (the TCP measured . T_tcp_obj) and the body frame where the
    # simulator has it: T_obj_tool written in the body frame, carried into the box frame the hold is in
    tcp, R = rig.kin.tcp(rig.q())
    T_tcp = np.eye(4)
    T_tcp[:3, :3], T_tcp[:3, 3] = R, tcp
    T_box = T_tcp @ np.asarray(held.T_tcp_obj, float)
    p, quat = rig.obj_pose(name)
    T_body = np.eye(4)
    T_body[:3, :3], T_body[:3, 3] = quat_R(quat), np.asarray(p, float)
    T_obj_tool = np.eye(4)
    T_obj_tool[:3, 3] = np.asarray(frames[frame], float)
    return np.asarray(held.T_tcp_obj, float) @ np.linalg.inv(T_box) @ T_body @ T_obj_tool
