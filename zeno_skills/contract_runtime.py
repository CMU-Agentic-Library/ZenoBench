"""Measured contract calls over the existing atomic policy routes.

A contract groups alternative physical routes; each route remains an independent
policy class. The runner checks a small shared pre/postcondition set and leaves
all state changes visible if a policy fails so an upper layer can replan.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .contracts import CONTRACTS
from .rig import SkillFailure
from . import skills


@dataclass(frozen=True)
class ContractResult:
    contract_id: str
    route: str
    success: bool
    observations: dict
    error: str | None = None


class ContractRunner:
    """Execute one contract route at a time and record measured outcomes."""

    def __init__(self, rig):
        self.rig = rig
        self.trace: list[ContractResult] = []

    def run(self, contract_id: str, route: str, *args, **kwargs) -> ContractResult:
        spec = CONTRACTS[contract_id]
        policy = spec.bind(self.rig, route)
        try:
            before = self._before(contract_id, route, args)
            policy.execute(*args, **kwargs)
            observations = self._verify(contract_id, route, args, kwargs, before)
        except Exception as exc:
            self.trace.append(ContractResult(contract_id, route, False, {}, str(exc)))
            raise
        result = ContractResult(contract_id, route, True, observations)
        self.trace.append(result)
        return result

    def _before(self, contract_id, route, args):
        rig = self.rig
        kind = contract_id.split(".", 1)[0]
        result = {"held": None if rig.held is None else rig.held["name"],
                  "left_held": None if rig.left_held is None else rig.left_held["name"],
                  "events": len(rig.events)}
        if kind in ("pick", "push"):
            name = args[0]
            if kind == "pick" and rig.held is not None:
                raise SkillFailure("pick contract: right hand is occupied")
            if kind == "push" and rig.held is not None:
                raise SkillFailure("push contract: right hand is occupied")
            result["object_pos"] = rig.obj_pose(name)[0].copy()
        if kind == "place":
            if rig.held is None or rig.held["name"] != args[0]:
                raise SkillFailure("place contract: object is not right-held")
        if kind in ("open", "close"):
            art_name = args[1] if kind == "open" and route == "while_left_holds" else args[0]
            rig.ann.art(art_name)
        if kind == "click" and rig.held is not None:
            raise SkillFailure("click contract: right hand is occupied")
        return result

    def _verify(self, contract_id, route, args, kwargs, before):
        rig = self.rig
        kind = contract_id.split(".", 1)[0]
        if kind == "navigate":
            goal = args[1] if route == "two_hand_carry" else args[0]
            x, y, yaw = rig.base_pose()
            xy_error = math.hypot(x-goal[0], y-goal[1])
            yaw_error = abs((yaw-goal[2]+180) % 360-180)
            if xy_error > 0.05 or yaw_error > 5:
                raise SkillFailure("navigate contract: base missed target")
            if before["held"] != (None if rig.held is None else rig.held["name"]):
                raise SkillFailure("navigate contract: right-held object changed")
            if before["left_held"] != (None if rig.left_held is None else rig.left_held["name"]):
                raise SkillFailure("navigate contract: left-held object changed")
            if rig.held is not None:
                skills.check_held(rig, "navigate_contract")
            if rig.left_held is not None:
                skills.check_left_held(rig, "navigate_contract")
            return {"base_pose": [x, y, yaw], "xy_error_m": xy_error,
                    "yaw_error_deg": yaw_error}
        if kind == "pick":
            name = args[0]
            if rig.held is None or rig.held["name"] != name:
                raise SkillFailure("pick contract: requested object is not right-held")
            skills.check_held(rig, "pick_contract")
            lift = float(rig.obj_pose(name)[0][2]-before["object_pos"][2])
            if lift < 0.015:
                raise SkillFailure("pick contract: object did not lift")
            return {"object": name, "lift_m": lift,
                    "fingers_m": rig.fingers().tolist()}
        if kind == "place":
            name, target = args[:2]
            if rig.held is not None and rig.held["name"] == name:
                raise SkillFailure("place contract: right hand still holds object")
            state = rig.state()
            if target.startswith("in:"):
                ok, detail = rig.geo.inside(name, target[3:], state)
            else:
                ok, detail = rig.geo.on(name, target, state)
            if not ok:
                raise SkillFailure(f"place contract: target predicate false ({detail})")
            return {"object": name, "target": target, "geometry": detail}
        if kind in ("open", "close"):
            name = args[1] if kind == "open" and route == "while_left_holds" else args[0]
            art = rig.ann.art(name)
            q = rig.joint(name)
            goal = art["open_q"] if kind == "open" else art["closed_q"]
            if kind == "open" and kwargs.get("goal") is not None:
                goal = kwargs["goal"]
            tol = 0.10 if art["type"] == "revolute" else (
                0.4*abs(art["open_q"]-art["closed_q"]) if kind == "open" else 0.04)
            if abs(q-goal) >= tol:
                raise SkillFailure(f"{kind} contract: measured joint {q:.3f}, goal {goal:.3f}")
            if route == "while_left_holds":
                if before["left_held"] != args[0] or rig.left_held is None or rig.left_held["name"] != args[0]:
                    raise SkillFailure("open contract: left-held object changed")
                skills.check_left_held(rig, "open_contract")
            return {"articulated": name, "joint": q, "goal": goal}
        if kind == "push":
            name, _, direction, distance = args[:4]
            direction = np.asarray(direction, float)
            progress = float((rig.obj_pose(name)[0]-before["object_pos"])[:2] @ direction)
            minimum = kwargs.get("enough", max(0.01, float(distance)*0.5))
            if progress < minimum:
                raise SkillFailure(f"push contract: only {progress:.3f} m progress")
            return {"object": name, "progress_m": progress}
        if kind == "click":
            button = "start" if route == "start" else kwargs.get("button", "door")
            label = "microwave_start" if button == "start" else "microwave_door_button"
            if not any(e["label"] == label for e in rig.events[before["events"]:]):
                raise SkillFailure("click contract: no fresh measured button event")
            if button == "start" and (rig.thermal is None or not rig.thermal.active):
                raise SkillFailure("click contract: heating is not active")
            return {"button": button, "event": label}
        if kind == "set_posture":
            if route == "tuck":
                error = float(np.max(np.abs(rig.q()-rig.kin.rest)))
            else:
                idx = rig.kin.names.index("waist_pitch_joint" if route in
                    ("waist", "lean", "straighten") else "torso_lift_joint")
                target = (0.0 if route == "straighten" else
                    args[0] if args and args[0] is not None else
                    rig.kin.lo[idx] if route == "lower" else rig.kin.hi[idx])
                error = abs(float(rig.q()[idx])-float(target))
            if error > (0.05 if route == "tuck" else 0.035):
                raise SkillFailure(f"posture contract: measured joint error {error:.3f}")
            return {"joint_error": error}
        raise ValueError(f"unknown contract {contract_id}")
