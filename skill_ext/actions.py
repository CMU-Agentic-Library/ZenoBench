"""Action interface for policy executors (VLA / RL / scripted policy).

The policy never touches the simulator directly: one action per step, clipped and executed through
the rig's own collision-checked motion (``Rig.move_to`` -> cuRobo, ``Rig.grip``).  A motion the
planner cannot produce is reported back to the policy (``ok: False``), not raised.
"""
from __future__ import annotations

import numpy as np

MAX_EE_STEP_M = 0.03          # per action
MAX_JOINT_STEP_RAD = 0.08
OPEN_W, CLOSED_W = 0.04, 0.0
GRASP_RADIUS_M = 0.06         # a closed hand holds the object whose centre is this close to the TCP


def proprio(rig) -> dict:
    p, R = rig.kin.tcp(rig.q_cmd)
    return {"tcp_pos": [round(float(v), 4) for v in p], "tcp_R": [round(float(v), 4) for v in np.asarray(R).ravel()],
            "fingers": [round(float(v), 4) for v in rig.fingers()],
            "arm_q": [round(float(v), 4) for v in rig.q_cmd],
            "base_pose": [round(float(v), 3) for v in rig.base_pose()],
            "held_right": (rig.held or {}).get("name")}


def _close_hand(rig, width):
    from zeno_skills.rig import SkillFailure  # noqa: F401  (import check: rig module loaded)
    f = rig.grip(width)
    if rig.held is None and float(sum(f)) > 0.002:
        p, R = rig.kin.tcp(rig.q_cmd)
        st = rig.state()
        best = None
        for n, o in st["objects"].items():
            d = float(np.linalg.norm(np.asarray(o["pos"]) - p))
            if d < GRASP_RADIUS_M and (best is None or d < best[1]):
                best = (n, d)
        if best is not None:
            body = np.asarray(st["objects"][best[0]]["pos"])
            rig.held = {"name": best[0], "kind": "pinch", "tcp_minus_body": p - body, "R": R, "pre_open": OPEN_W}
            rig.log("policy_grasp", name=best[0], d=round(best[1], 3))
    return f


def _gripper(rig, g):
    if g is None:
        return
    if g == "open" or (isinstance(g, (int, float)) and g >= OPEN_W - 1e-6):
        rig.grip(OPEN_W)
        if rig.held is not None:
            rig.log("policy_release", name=rig.held.get("name"))
            rig.held = None
    elif g == "close":
        _close_hand(rig, CLOSED_W)
    else:
        _close_hand(rig, float(g))


def execute(rig, space: str, action: dict, call_skill) -> dict:
    """One action.  Returns {"ok", "error"?, "fatal"?}."""
    from zeno_skills.rig import SkillFailure
    try:
        if space == "skill_calls":
            res = call_skill(action["skill"], action.get("args", {}))
            return {"ok": bool(res["success"]), "error": res.get("error")}
        if space == "ee_delta" and action.get("ee_delta") is not None:
            d = np.clip(np.asarray(action["ee_delta"], float)[:3], -MAX_EE_STEP_M, MAX_EE_STEP_M)
            p, R = rig.kin.tcp(rig.q_cmd)
            rig.move_to(p + d, R, label="user_policy")
        elif space == "joint_delta" and action.get("joint_delta") is not None:
            d = np.clip(np.asarray(action["joint_delta"], float), -MAX_JOINT_STEP_RAD, MAX_JOINT_STEP_RAD)
            q = np.asarray(rig.q_cmd, float).copy()
            q[:len(d)] += d
            rig.follow([q])
        _gripper(rig, action.get("gripper"))
        return {"ok": True}
    except SkillFailure as exc:
        return {"ok": False, "error": str(exc)}
    except Exception as exc:                          # a malformed action is the policy's fault, not the sim's
        return {"ok": False, "fatal": True, "error": f"{type(exc).__name__}: {exc}"}
