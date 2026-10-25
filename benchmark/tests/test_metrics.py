"""Offline tests of the EVALUATION_SPEC statistics (benchmark/metrics.py); no simulator.

    python -m pytest -q benchmark/tests/test_metrics.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from benchmark.metrics import call_eval, episode_facts, failed_substep, spec_markdown, spec_summary  # noqa: E402

CAB = "kitchen_cabinet_6/top"
T04 = {"task_id": "T04_cup_or_mug_to_cabinet",
       "goal": {"any": [[["on", "cup_counter_b", CAB], ["upright", "cup_counter_b"]],
                        [["on", "mug", CAB], ["upright", "mug"]]], "all": [["hand_empty", "right"]]},
       "variants": {"cup_available": {"conditions": [], "decisions": ["none"]},
                    "no_cup": {"conditions": ["no_cup"], "decisions": ["alternative"], "remove": ["cup_counter_b"]}},
       "routes": {}}
T01 = {"task_id": "T01_book_to_dining_table",
       "goal": {"all": [["on", "paperback_book", "table"], ["hand_empty", "right"]]},
       "variants": {"no_overhang": {"conditions": ["no_overhang"], "decisions": ["fallback"]}},
       "routes": {"fallback_expose": {"kind": "fallback", "variants": ["no_overhang"], "steps": [
           {"skill": "pick", "args": {"object": "paperback_book"}, "expect": "fail"},
           {"skill": "expose", "args": {"object": "paperback_book"}},
           {"skill": "pick", "args": {"object": "paperback_book"}}]}}}


def call(skill, args, ok=True, code=None, error=None, checks=(), state=None, **kw):
    fb = {"action": f"{skill}_x(" + ", ".join(f"{k}={v}" for k, v in args.items()) + ")", "success": ok,
          "error_code": code, "error": error, "checks": [{"atom": a, "holds": h, "detail": ""} for a, h in checks],
          "substeps": [], "now_visible": kw.pop("visible", [])}
    return {"skill": skill, "args": args, "feedback": fb, "state": state, **kw}


def book(x, on="island", held=None, base=(7.4, 1.0, 75.0)):
    return {"base": list(base), "held": [held, None], "paperback_book": {"pos": [x, 1.6, 0.87], "on": on}}


def result(task, variant, calls, success, goal=None, planner="recovery", **kw):
    return {"task_id": task["task_id"], "variant": variant, "seed": 10, "planner": planner, "route": None,
            "calls": calls, "task_success": success, "goal": goal or {"all": [], "any": []}, **kw}


def any_goal(cup, mug):
    return {"all": [{"atom": "hand_empty(right)", "holds": True}],
            "any": [[{"atom": "on(cup)", "holds": cup}, {"atom": "upright(cup)", "holds": cup}],
                    [{"atom": "on(mug)", "holds": mug}, {"atom": "upright(mug)", "holds": mug}]]}


CTX = {"feasible": {("T04_cup_or_mug_to_cabinet", "no_cup"), ("T04_cup_or_mug_to_cabinet", "cup_available"),
                    ("T01_book_to_dining_table", "no_overhang")},
       "alt_feasible": {("T04_cup_or_mug_to_cabinet", "no_cup")},
       "feasible_routes": {("T01_book_to_dining_table", "no_overhang", "fallback_expose")}}


def test_mug_while_cup_present_is_not_success():
    r = result(T04, "cup_available", [call("pick", {"object": "mug"}), call("place", {"object": "mug", "receptacle": CAB})],
               True, any_goal(False, True))
    f = episode_facts(r, T04, dict(CTX, objects={"cup_counter_b", "mug"}))
    assert f["physical_success"] and not f["task_success"]
    assert f["attribution"] == "substitution_failure"


def test_proactive_mug_when_no_cup_is_alternative_success():
    r = result(T04, "no_cup", [call("pick", {"object": "mug"}), call("place", {"object": "mug", "receptacle": CAB})],
               True, any_goal(False, True), _removed=["cup_counter_b"])
    f = episode_facts(r, T04, dict(CTX, objects={"mug"}))
    assert f["task_success"] and f["success_type"] == "alternative" and not f["had_failure"]
    s = spec_summary([f])
    assert s["FSR"]["rate"] == {"num": 1, "den": 1, "value": 1.0}
    assert s["FSR"]["proactive"] == 1


def test_substitute_selected_then_dropped_is_selection_ok_task_failed():
    r = result(T04, "no_cup", [call("pick", {"object": "mug"}),
                               call("place", {"object": "mug", "receptacle": CAB}, ok=False, code="POLICY_FAILED",
                                    error="slipped")], False, any_goal(False, False), _removed=["cup_counter_b"])
    f = episode_facts(r, T04, dict(CTX, objects={"mug"}))
    s = spec_summary([f])
    assert s["FSR"]["selection"]["num"] == 1 and s["FSR"]["rate"]["num"] == 0
    assert f["attribution"] == "low_level_execution_failure"


def test_aux_recovery_then_carry_failure():
    """Pick fails -> Expose moves the book -> Pick ok -> place slips: local recovery, task failed."""
    calls = [call("pick", {"object": "paperback_book"}, ok=False, code="POLICY_FAILED", error="not held",
                  state=book(7.62)),
             call("expose", {"object": "paperback_book"}, state=book(7.55)),
             call("pick", {"object": "paperback_book"}, state=book(7.55, held="paperback_book")),
             call("place", {"object": "paperback_book", "receptacle": "table"}, ok=False, code="POLICY_FAILED",
                  error="flat_back_out: slipped", state=book(3.7, on="floor"))]
    f = episode_facts(result(T01, "no_overhang", calls, False), T01, CTX)
    first, last = f["events"]
    assert first["outcome"] == "local_recovery" and "moved: paperback_book" in first["evidence"]
    assert last["outcome"] == "not_recovered"
    assert f["attribution"] == "low_level_execution_failure"      # not "Expose was the wrong choice"
    s = spec_summary([f])
    assert s["recovery"]["execution"]["local_recovery_but_task_failed"] == 1
    assert s["ERSR"] == {"num": 0, "den": 1, "value": 0.0}


def test_blind_retry_is_not_a_verified_recovery():
    st = book(7.62)
    calls = [call("pick", {"object": "paperback_book"}, ok=False, code="POLICY_FAILED", error="not held", state=st),
             call("pick", {"object": "paperback_book"}, state=book(7.62, held="paperback_book")),
             call("place", {"object": "paperback_book", "receptacle": "table"}, state=book(3.7, on="table"))]
    f = episode_facts(result(T01, "no_overhang", calls, True), T01, CTX)
    assert f["task_success"] and f["events"][0]["outcome"] == "retry_only"
    assert f["success_type"] == "recovered_unverified"


def test_identical_repeat_without_change_is_recovery_failure():
    st = book(7.62)
    calls = [call("pick", {"object": "paperback_book"}, ok=False, code="POLICY_FAILED", error="not held", state=st)
             for _ in range(3)]
    for c in calls:
        c["state_before"] = st
    f = episode_facts(result(T01, "no_overhang", calls, False, stop_reason="budget"), T01, CTX)
    assert f["attribution"] == "recovery_failure"
    assert f["efficiency"]["invalid_repeats"] == 2


def test_scripted_route_failure_is_not_blamed_on_a_planner():
    calls = [call("pick", {"object": "paperback_book"}, ok=False, code="POLICY_FAILED", error="not held",
                  state=book(7.62), expect="fail")]
    f = episode_facts(result(T01, "no_overhang", calls, False, planner="scripted", stopped_at=0), T01, CTX)
    assert f["attribution"] == "low_level_execution_failure"


def test_hand_occupied_precondition_is_planning_error():
    calls = [call("pick", {"object": "paperback_book"}, ok=False, code="PRECONDITION_FAILED",
                  error="PRECONDITION_FAILED: hand_empty(hand=right) is false", checks=[("hand_empty(hand=right)", False)])]
    f = episode_facts(result(T01, "no_overhang", calls, False), T01, CTX)
    assert f["plan"]["invalid"] == 1 and f["attribution"] == "planning_failure"
    s = spec_summary([f])
    assert s["planning"]["correctness"] == {"num": 0, "den": 1, "value": 0.0}


def test_observation_refusal_then_search_is_observation_recovery():
    calls = [call("pick", {"object": "paperback_book"}, ok=False, code="NOT_OBSERVED", error="NOT_OBSERVED: x"),
             call("search", {"object": "paperback_book"}, visible=["paperback_book"]),
             call("pick", {"object": "paperback_book"}),
             call("place", {"object": "paperback_book", "receptacle": "table"})]
    f = episode_facts(result(T01, "no_overhang", calls, True), T01, CTX)
    assert f["events"][0]["class"] == "observation" and f["events"][0]["outcome"] == "local_recovery"
    assert f["success_type"] == "fallback" and f["fallback_subtypes"] == ["observation"]
    s = spec_summary([f])
    assert s["ERSR"]["den"] == 0 and s["ERSR"]["value"] is None          # observation is not ERSR
    assert s["recovery"]["observation"]["task_success_after_failure"]["num"] == 1


def test_search_alone_without_failure_is_direct():
    calls = [call("search", {"object": "paperback_book"}, visible=["paperback_book"]),
             call("pick", {"object": "paperback_book"}), call("place", {"object": "paperback_book", "receptacle": "t"})]
    f = episode_facts(result(T01, "no_overhang", calls, True), T01, CTX)
    assert f["success_type"] == "direct"


def test_nested_failed_substep_from_error_text():
    fb = {"action": "hide_object(object=b)", "error_code": "SUBSKILL_FAILED",
          "error": "SUBSKILL_FAILED: fetch_object(object=b, receptacle=pot): SUBSKILL_FAILED: pick_object(object=b): "
                   "pick b: not held (lift 0.000 m)"}
    chain, code, leaf = failed_substep(fb)
    assert chain == ["hide_object(object=b)", "fetch_object(object=b, receptacle=pot)", "pick_object(object=b)"]
    assert code == "POLICY_FAILED" and leaf.startswith("pick b")
    fb2 = dict(fb, error="SUBSKILL_FAILED: collect_objects(objects=['a', 'b'], container=pot): "
                         "PRECONDITION_FAILED: uncovered(container=pot) is false")
    assert failed_substep(fb2)[1] == "PRECONDITION_FAILED"


def test_call_eval_walks_children():
    res = {"action": "hide(b)", "success": False, "error_code": "SUBSKILL_FAILED", "error": "x",
           "children": [{"action": "fetch(b)", "success": False, "error_code": "SUBSKILL_FAILED", "error": "y",
                         "children": [{"action": "pick(b)", "success": False, "error_code": "POLICY_FAILED",
                                       "error": "not held", "children": [],
                                       "preconditions": [{"atom": "grasp_clearance(b)", "holds": False}]}]}]}
    ev = call_eval(res)
    assert ev["failed_substep"] == ["hide(b)", "fetch(b)", "pick(b)"] and ev["leaf_code"] == "POLICY_FAILED"
    assert ev["failed_checks"] == ["grasp_clearance(b)"]


def test_old_log_without_state_reports_na():
    calls = [{"skill": "pick", "args": {"object": "paperback_book"},
              "feedback": {"action": "pick", "success": True}}]
    f = episode_facts(result(T01, "no_overhang", calls, True), T01, {})
    assert f["efficiency"]["nav_m_lower_bound"] is None and f["efficiency"]["room_transitions"] is None
    s = spec_summary([f])
    assert s["FSR"]["rate"]["value"] is None and s["efficiency"]["success"]["planner_s"]["mean"] is None
    md = "\n".join(spec_markdown({"recovery": s}))
    assert "N/A" in md


def test_system_error_leaves_the_denominator():
    ok = episode_facts(result(T01, "no_overhang", [], True), T01, CTX)
    crash = episode_facts(result(T01, "no_overhang", [], False, crash="RuntimeError: Isaac", incomplete=True), T01, CTX)
    s = spec_summary([ok, crash], planned=3)
    assert s["counts"] == {"planned": 3, "started": 2, "valid": 1, "system_error": 1}
    assert s["TSR"]["overall"] == {"num": 1, "den": 1, "value": 1.0}


def test_registry_semantics_cover_every_alternative_condition():
    """Every v3 variant whose decision is "alternative" has a declared legal substitute."""
    from benchmark.eval_semantics import SEMANTICS
    doc = json.loads((ROOT / "benchmark/v3/tasks.json").read_text())
    for t in doc["tasks"]:
        for name, v in t["variants"].items():
            if "alternative" in (v.get("decisions") or []):
                sem = SEMANTICS.get(t["task_id"])
                assert sem, t["task_id"]
                assert any(c in sem["substitute"] for c in v.get("conditions") or []), (t["task_id"], name)


def test_changed_grasp_and_unlisted_helper_can_recover():
    calls = [call("pick", {"object": "paperback_book"}, ok=False, code="POLICY_FAILED", state=book(7.62)),
             call("pull", {"object": "paperback_book"}, state=book(7.50)),
             call("pick", {"object": "paperback_book", "grasp": "edge"},
                  state=book(7.50, held="paperback_book"))]
    f = episode_facts(result(T01, "no_overhang", calls, True), T01, CTX)
    ev = f["events"][0]
    assert ev["outcome"] == "local_recovery" and ev["resolution"] == "equivalent_outcome"
    assert ev["helpers"] == ["pull"] and ev["recovered_at"] == 2


def test_composite_finishing_goal_does_not_need_an_explicit_pick_retry():
    calls = [call("pick", {"object": "paperback_book"}, ok=False, code="POLICY_FAILED", state=book(7.62)),
             call("fetch", {"object": "paperback_book", "receptacle": "table"}, state=book(3.7, on="table"))]
    goal = {"all": [{"atom": "on(paperback_book, table)", "holds": True},
                    {"atom": "hand_empty(right)", "holds": True}], "any": []}
    f = episode_facts(result(T01, "no_overhang", calls, True, goal), T01, CTX)
    assert f["success_type"] == "fallback"
    assert f["events"][0]["resolution"] == "task_goal"
    assert f["local_recovery"] == 0 and f["goal_recovery"] == 1
    summary = spec_summary([f])["recovery"]["execution"]
    assert summary["local_recovery"]["num"] == 0 and summary["goal_recovery"] == 1
    assert summary["verified_task_success_after_failure"]["num"] == 1
    assert "intermediate skill outcome not inferred" in f["events"][0]["evidence"][0]


def test_alternative_completed_by_fetch_without_pick_or_place_calls():
    r = result(T04, "no_cup", [call("fetch", {"object": "mug", "receptacle": CAB})],
               True, any_goal(False, True), _removed=["cup_counter_b"])
    f = episode_facts(r, T04, dict(CTX, objects={"mug"}))
    assert f["task_success"] and f["success_type"] == "alternative"
    summary = spec_summary([f])["FSR"]
    assert summary["rate"]["num"] == 1 and summary["selection"]["num"] == 1
    assert summary["selection_timing_unknown"] == 1 and summary["proactive"] == 0


def test_selection_uses_holding_effect_not_pick_name():
    before = {"held": [None, "mug"]}
    after = {"held": ["mug", None]}
    r = result(T04, "no_cup", [call("handover", {"object": "mug", "to": "right"},
                                   state_before=before, state=after)],
               False, any_goal(False, False), _removed=["cup_counter_b"])
    f = episode_facts(r, T04, dict(CTX, objects={"mug"}))
    assert f["substitution"]["selected"] and not f["substitution"]["used_substitution"]
    assert spec_summary([f])["FSR"]["selected_but_failed"] == 1


def test_composite_does_not_bypass_preferred_object_semantics():
    r = result(T04, "cup_available", [call("fetch", {"object": "mug", "receptacle": CAB})],
               True, any_goal(False, True))
    f = episode_facts(r, T04, dict(CTX, objects={"mug", "cup_counter_b"}))
    assert not f["task_success"] and f["attribution"] == "substitution_failure"


def test_stove_outcome_without_heat_skill_is_a_valid_method_alternative():
    task = {"task_id": "T07_heat_oatmeal", "variants": {"broken": {"conditions": ["microwave_broken"]}},
            "goal": {"all": [["temperature_at_least", "oatmeal", 40]]}}
    before = {"oatmeal": {"on": "kitchen_stove/top"}, "temp_c": {"oatmeal": 4}}
    after = {"oatmeal": {"on": "kitchen_stove/top"}, "temp_c": {"oatmeal": 45}}
    r = result(task, "broken", [call("wait", {}, state_before=before, state=after)], True,
               {"all": [{"atom": "temperature_at_least(oatmeal, 40)", "holds": True}]})
    f = episode_facts(r, task, {"alt_feasible": {(task["task_id"], "broken")}})
    assert f["substitution"]["used"] == ["stove"]
    assert spec_summary([f])["FSR"]["rate"]["num"] == 1


def test_heat_name_without_food_temperature_evidence_does_not_prove_alternative():
    task = {"task_id": "T07_heat_oatmeal", "variants": {"broken": {"conditions": ["microwave_broken"]}}}
    r = result(task, "broken", [call("heat", {"food": "mug", "appliance": "kitchen_stove", "temp_c": 40})], False)
    f = episode_facts(r, task, {"alt_feasible": {(task["task_id"], "broken")}})
    assert not f["substitution"]["used_substitution"]
    assert not f["substitution"]["selected"]


def test_unrelated_motion_is_not_repair_evidence():
    st = dict(book(7.62), rolling_pin={"pos": [1, 1, 1]})
    st2 = dict(book(7.62), rolling_pin={"pos": [2, 1, 1]})
    calls = [call("pick", {"object": "paperback_book"}, ok=False, code="POLICY_FAILED", state=st),
             call("push", {"object": "rolling_pin"}, state=st2),
             call("pick", {"object": "paperback_book"}, state=book(7.62, held="paperback_book"))]
    f = episode_facts(result(T01, "no_overhang", calls, True), T01, CTX)
    assert f["events"][0]["outcome"] == "mechanism_unverified"


def test_picking_substitute_without_resolving_goal_is_not_alternative_recovery():
    calls = [call("pick", {"object": "cup_counter_b"}, ok=False, code="NOT_OBSERVED"),
             call("pick", {"object": "mug"})]
    f = episode_facts(result(T04, "no_cup", calls, False, any_goal(False, False), _removed=["cup_counter_b"]),
                      T04, dict(CTX, objects={"mug"}))
    assert f["substitution"]["selected"]
    assert f["events"][0]["outcome"] == "not_recovered"


def test_blind_retry_keeps_broad_ersr_but_not_verified_recovery_score():
    calls = [call("pick", {"object": "paperback_book"}, ok=False, code="POLICY_FAILED", state=book(7.62)),
             call("pick", {"object": "paperback_book"}, state=book(7.62, held="paperback_book"))]
    f = episode_facts(result(T01, "no_overhang", calls, True), T01, CTX)
    summary = spec_summary([f])
    assert summary["ERSR"]["num"] == 1
    assert summary["recovery"]["execution"]["verified_task_success_after_failure"]["num"] == 0


def test_stale_precondition_cannot_prove_recovery_effect():
    calls = [call("pick", {"object": "paperback_book"}, ok=False, code="POLICY_FAILED", state=book(7.62)),
             call("place", {"object": "paperback_book", "receptacle": "other"}, state=book(7.62),
                  checks=[("holding(hand=right, object=paperback_book)", True)])]
    f = episode_facts(result(T01, "no_overhang", calls, False), T01, CTX)
    assert f["events"][0]["outcome"] == "not_recovered"


def test_goal_completion_never_overrides_failed_final_verifier():
    calls = [call("pick", {"object": "paperback_book"}, ok=False, code="POLICY_FAILED", state=book(7.62)),
             call("fetch", {"object": "paperback_book", "receptacle": "table"}, state=book(3.7, on="floor"))]
    goal = {"all": [{"atom": "on(paperback_book, table)", "holds": False}]}
    f = episode_facts(result(T01, "no_overhang", calls, False, goal), T01, CTX)
    assert not f["task_success"] and f["events"][0]["outcome"] == "not_recovered"


def test_multiple_legal_alternative_results_not_just_one_reference_route():
    task = {"task_id": "custom", "goal": {"any": [[["inside", "toy", "box"]], [["inside", "toy", "tray"]]]},
            "variants": {"missing": {"conditions": ["basket_missing"]}}}
    semantics = {"custom": {"kind": "either", "options": {"box": {"groups": [0]}, "tray": {"groups": [1]}},
                            "substitute": {"basket_missing": ["box", "tray"]}}}
    for index in range(2):
        goal = {"any": [[{"atom": "inside(toy, box)", "holds": index == 0}],
                        [{"atom": "inside(toy, tray)", "holds": index == 1}]]}
        r = result(task, "missing", [], True, goal)
        f = episode_facts(r, task, {"semantics": semantics, "alt_feasible": {("custom", "missing")}})
        assert f["success_type"] == "alternative" and spec_summary([f])["FSR"]["rate"]["num"] == 1


def test_nested_leaf_recovery_can_use_changed_parameters():
    calls = [call("hide", {"object": "paperback_book", "receptacle": "pot"}, ok=False,
                  code="SUBSKILL_FAILED", state=book(7.62),
                  error="SUBSKILL_FAILED: fetch_object(object=paperback_book, receptacle=pot): "
                        "SUBSKILL_FAILED: pick_object(object=paperback_book): pick failed"),
             call("pull", {"object": "paperback_book"}, state=book(7.5)),
             call("pick", {"object": "paperback_book", "grasp": "edge"}, state=book(7.5, held="paperback_book"))]
    f = episode_facts(result(T01, "no_overhang", calls, False), T01, CTX)
    assert f["events"][0]["outcome"] == "local_recovery"
    assert f["events"][0]["resolution"] == "equivalent_outcome"


def test_destination_clearance_can_finish_without_selecting_the_alternative():
    task = {"task_id": "T06_block_destination_occupied", "goal": {"any": [[["on", "wooden_block_a", CAB]],
                    [["on", "wooden_block_a", "tv_stand_2/top"]]]},
            "variants": {"occupied": {"conditions": ["destination_occupied"]}}}
    goal = {"any": [[{"atom": "on(wooden_block_a, cabinet)", "holds": True}],
                    [{"atom": "on(wooden_block_a, tv)", "holds": False}]]}
    f = episode_facts(result(task, "occupied", [], True, goal), task,
                      {"alt_feasible": {(task["task_id"], "occupied")}})
    assert f["task_success"] and not f["substitution"]["used_substitution"]
    assert spec_summary([f])["FSR"]["rate"]["num"] == 0


def test_already_satisfied_goal_branch_is_not_a_new_recovery():
    task = {"task_id": "custom", "goal": {"any": [[["on", "paperback_book", "table"]],
                                                 [["on", "paperback_book", "shelf"]]]},
            "variants": {"normal": {}}}
    st = book(3.7, on="table")
    calls = [call("pick", {"object": "paperback_book"}, ok=False, code="POLICY_FAILED", state=st),
             call("look", {"target": "table"}, state=st)]
    goal = {"any": [[{"atom": "on(paperback_book, table)", "holds": True}],
                    [{"atom": "on(paperback_book, shelf)", "holds": False}]]}
    f = episode_facts(result(task, "normal", calls, True, goal), task)
    assert f["task_success"] and f["events"][0]["outcome"] == "not_recovered"
