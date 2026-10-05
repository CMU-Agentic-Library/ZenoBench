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
from .node_contracts import NODE_CONTRACTS
from .noun_binding import bind_contract_nouns, select_policy_path


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
        if contract_id in NODE_CONTRACTS:
            return self._run_node_contract(contract_id, route, args, kwargs)
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

    def run_bound(self, contract_id: str, **named_args) -> ContractResult:
        """Fill a Contract's named noun/value slots with grounded scene IDs."""
        if contract_id not in NODE_CONTRACTS:
            raise ValueError(f"{contract_id}: run_bound requires an active Skill Contract")
        order = NODE_CONTRACTS[contract_id]["legacy_call_args"]
        if set(named_args) != set(order):
            raise ValueError(f"{contract_id}: expected named inputs {order}")
        return self.run(contract_id, "compose", *(named_args[name] for name in order))

    def _run_node_contract(self, contract_id, route, args, kwargs):
        """Run a local policy sequence, then verify its advertised state change."""
        from .policies import PolicySuite

        row = NODE_CONTRACTS[contract_id]
        if route != "compose" or kwargs:
            raise ValueError(f"{contract_id}: expected compose route without keyword arguments")
        order = row["legacy_call_args"]
        if len(args) != len(order):
            raise ValueError(f"{contract_id}: expected {len(order)} arguments")
        values = dict(zip(order, args))
        verifier = row["verifier"]
        family_id = resolve_contract_id(verifier["legacy_family_contract"]) if verifier.get("legacy_family_contract") else None
        family_route = verifier.get("route", "compose")
        family_order = verifier.get("family_arg_order", order)
        family_args = tuple(
            row["argument_transforms"].get(name, "") + values[name]
            if name in row["argument_transforms"] else values[name]
            for name in family_order
        )
        completed = []
        failed_step = None
        noun_context = {}
        selected_path = None
        try:
            noun_context = bind_contract_nouns(row, values, self.rig)
            before = (self._before(family_id, family_route, family_args) if family_id
                      else {"base_pose": tuple(self.rig.base_pose()),
                            "held": None if self.rig.held is None else self.rig.held["name"],
                            "events": len(self.rig.events)})
            selected_path, steps = select_policy_path(row["policy_plan"], noun_context)
            suite = PolicySuite(self.rig)
            for index, step in enumerate(steps, 1):
                failed_step = {"index": index, "policy_id": step["policy_id"]}
                policy_args = [values[item["arg"]] for item in step["args"]]
                policy_kwargs = {
                    name: values[value["arg"]] if isinstance(value, dict) else value
                    for name, value in step.get("kwargs", {}).items()
                }
                getattr(suite, step["policy_id"]).execute(*policy_args, **policy_kwargs)
                completed.append(failed_step)
                failed_step = None
            observations = (self._verify(family_id, family_route, family_args, {}, before)
                            if family_id else {})
            observations.update(self._verify_node_effects(verifier, values, before))
            observations["verified_predicates"] = [
                item["predicate"] for item in row["achieves"]
            ]
            observations["policy_steps"] = completed
            observations["bound_nouns"] = noun_context
            observations["selected_policy_path"] = selected_path
        except Exception as exc:
            snapshot = self._after_snapshot(family_id or "node.v1", family_route, family_args)
            snapshot["completed_policy_steps"] = completed
            snapshot["failed_policy_step"] = failed_step
            snapshot["bound_nouns"] = noun_context
            snapshot["selected_policy_path"] = selected_path
            self.trace.append(ContractResult(
                contract_id, route, False, snapshot, str(exc), type(exc).__name__
            ))
            raise
        result = ContractResult(contract_id, route, True, observations)
        self.trace.append(result)
        return result

    def _verify_node_effects(self, verifier, values, before):
        """Check extra effects that are not part of the eight legacy families."""
        from .evaluator import tilt_deg

        rig = self.rig
        checks = list(verifier.get("extra_checks", []))
        if verifier.get("custom"):
            checks.append(verifier["custom"])
        out = {}
        for check in checks:
            if check == "upright":
                name = values["object"]
                angle = float(tilt_deg(rig.obj_pose(name)[1]))
                if angle > 20.0:
                    raise SkillFailure(f"upright contract: {name} is tilted {angle:.1f} deg")
                out["object_tilt_deg"] = angle
            elif check == "within_hint":
                name = values["object"]
                bottom = rig.geo.bottom(name, rig.state())
                error = float(np.linalg.norm(bottom[:2] - np.asarray(values["hint_xy"], float)))
                if error > values["max_offset_m"]:
                    raise SkillFailure(f"near-hint contract: object is {error:.3f} m from hint")
                out["hint_error_m"] = error
            elif check == "temperature":
                thermal = rig.thermal
                name = values["object"]
                actual = float(thermal.temperatures_c[name])
                if actual < float(values["min_temp_c"]):
                    raise SkillFailure(f"temperature contract: {actual:.1f} C below target")
                out["temperature_c"] = actual
            elif check == "carry_height":
                held = rig.held
                if held is None or held["name"] != before["held"]:
                    raise SkillFailure("carry-height contract: held object changed")
                actual = float(rig.geo.bottom(held["name"], rig.state())[2])
                if actual < float(values["min_bottom_z"]) - 0.02:
                    raise SkillFailure("carry-height contract: object remains too low")
                out["held_bottom_z"] = actual
            elif check == "back_off":
                if rig.held is None or rig.held["name"] != before["held"]:
                    raise SkillFailure("back-off contract: held object changed")
                x0, y0, _ = before["base_pose"]
                x1, y1, _ = rig.base_pose()
                moved = math.hypot(x1 - x0, y1 - y0)
                if moved < 0.09:
                    raise SkillFailure("back-off contract: base did not move enough")
                out["base_moved_m"] = moved
            elif check == "edge_ready":
                name = values["object"]
                events = [e for e in rig.events[before["events"]:]
                          if e.get("label") == "slide_to_edge_result" and e.get("obj") == name]
                if not events:
                    raise SkillFailure("edge-ready contract: no fresh overhang measurement")
                event = events[-1]
                direction = np.asarray(event["direction"], float)
                st = rig.state()
                support = rig.geo.support_under(name, st)
                if support is None or support["name"] != event["support"]:
                    raise SkillFailure("edge-ready contract: support changed")
                obj = rig.ann.objects[name]
                size = np.asarray(rig.ann.asset_of(obj)["size"], float)
                bottom = rig.geo.bottom(name, st)
                half = skills._half_along(size, skills._yaw(st["objects"][name]["quat"]), direction)
                overhang = float(direction @ bottom[:2]) + half - skills._edge_coord(support, direction)
                if (overhang < skills.EDGE_MIN_OVERHANG - 0.01
                        or overhang > half - skills.COM_MARGIN + 0.015):
                    raise SkillFailure("edge-ready contract: current overhang is unsafe")
                out["overhang_m"] = overhang
            else:
                raise ValueError(f"unknown node verifier {check}")
        return out

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
