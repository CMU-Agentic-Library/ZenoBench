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
from .interface_ids import resolve_contract_id
from .rig import SkillFailure
from . import skills


@dataclass(frozen=True)
class ContractResult:
    contract_id: str
    route: str
    success: bool
    observations: dict
    error: str | None = None
    error_code: str | None = None


class ContractRunner:
    """Execute one contract route at a time and record measured outcomes."""

    def __init__(self, rig):
        self.rig = rig
        self.trace: list[ContractResult] = []

    def run(self, contract_id: str, route: str, *args, **kwargs) -> ContractResult:
        """Run a legacy family Contract route (contract_001..008).

        Planner-facing verb Contracts (contract_009 and up) go through
        :meth:`run_skill`, which checks their GT pre/postconditions."""
        if self._skill_runner().by_id.get(contract_id):
            raise ValueError(f"{contract_id} is a Skill Contract: use run_skill(contract_id, args)")
        legacy_id = resolve_contract_id(contract_id)
        try:
            spec = CONTRACTS[legacy_id]
            policy = spec.bind(self.rig, route)
            before = self._before(legacy_id, route, args)
            policy.execute(*args, **kwargs)
            observations = self._verify(legacy_id, route, args, kwargs, before)
            observations["verified_predicates"] = self._verified_predicates(
                spec, route, args, kwargs
            )
        except Exception as exc:
            self.trace.append(ContractResult(
                contract_id, route, False, self._after_snapshot(legacy_id, route, args),
                str(exc), type(exc).__name__
            ))
            raise
        result = ContractResult(contract_id, route, True, observations)
        self.trace.append(result)
        return result

    def _skill_runner(self):
        if getattr(self, "_skills", None) is None:
            from .skill_runtime import SkillContractRunner
            self._skills = SkillContractRunner(self.rig)
        return self._skills

    def run_skill(self, key: str, args: dict):
        """Run a verb Skill Contract (ID, skill ID or verb) with named inputs;
        raises ContractError with the measured report if it does not succeed."""
        result = self._skill_runner().run_or_raise(key, args)
        self.trace.append(ContractResult(result.contract_id, result.selected_path or "", True, result.asdict()))
        return result

    def run_bound(self, contract_id: str, **named_args):
        """Backward-compatible name for :meth:`run_skill`."""
        return self.run_skill(contract_id, named_args)

    @staticmethod
    def _verified_predicates(spec, route, args, kwargs):
        """Name only postconditions actually checked by this invocation."""
        target = args[1] if spec.id == "place.v1" and len(args) > 1 else ""
        button = "start" if route == "start" else kwargs.get("button", "door")
        names = []
        for row in spec.profile["achieves"]:
            if row["check"] != "runner":
                continue
            when = row.get("when")
            if when == "target starts with in:" and not target.startswith("in:"):
                continue
            if when == "target does not start with in:" and target.startswith("in:"):
                continue
            if when == "button is start" and button != "start":
                continue
            names.append(row["predicate"])
        return names

    def _after_snapshot(self, contract_id, route, args):
        """Best-effort measured state after failure, including partial effects."""
        rig = self.rig
        held = getattr(rig, "held", None)
        left_held = getattr(rig, "left_held", None)
        out = {
            "held_right": None if held is None else held.get("name"),
            "held_left": None if left_held is None else left_held.get("name"),
        }
        try:
            out["base_pose"] = [float(v) for v in rig.base_pose()]
        except Exception:
            pass
        try:
            out["scene_state"] = rig.state()
        except Exception:
            pass
        kind = contract_id.split(".", 1)[0]
        if args and kind in ("pick", "place", "push"):
            try:
                out["object"] = str(args[0])
                out["object_position"] = [float(v) for v in rig.obj_pose(args[0])[0]]
            except Exception:
                pass
        if args and kind in ("open", "close"):
            try:
                name = args[1] if kind == "open" and route == "while_left_holds" else args[0]
                out["joint"] = {"name": str(name), "position": float(rig.joint(name))}
            except Exception:
                pass
        return out

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
            target = args[1]
            if route == "container" and not target.startswith("in:"):
                raise SkillFailure("place contract: container target must start with in:")
            if route in ("surface", "edge") and target.startswith("in:"):
                raise SkillFailure("place contract: surface/edge route cannot target a container")
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
            if rig.held is not None:
                raise SkillFailure("place contract: right hand is not empty")
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
