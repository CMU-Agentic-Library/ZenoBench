"""Offline tests of the quantitative protocol (benchmark/protocol.py); no simulator.

    python -m pytest -q benchmark/tests/test_protocol.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from benchmark.metrics import episode_facts  # noqa: E402
from benchmark.protocol import protocol_markdown, protocol_summary, similarity  # noqa: E402
from benchmark.tests.test_metrics import CTX, T01, book, call, result  # noqa: E402

SHELF = "bookcase_2/top"
T14 = {"task_id": "T14_shelve_the_book",
       "goal": {"all": [["on", "book_red", SHELF], ["hand_empty", "right"]]},
       "variants": {"shelf_taken": {"conditions": ["destination_full"], "decisions": ["insert"]}},
       "routes": {"hard_make_room_first": {"kind": "alternative", "variants": ["shelf_taken"], "steps": [
           {"skill": "pick", "args": {"object": "mug_shelf"}},
           {"skill": "place", "args": {"object": "mug_shelf", "receptacle": SHELF, "hint_xy": [0.79, -0.31]}},
           {"skill": "pick", "args": {"object": "book_red"}},
           {"skill": "place", "args": {"object": "book_red", "receptacle": SHELF}}]}}}


def shelf(mug_x, book_on="desk", held=None):
    return {"base": [0.9, -1.1, 90.0], "held": [held, None],
            "mug_shelf": {"pos": [mug_x, -0.53, 0.77 if held != "mug_shelf" else 0.9],      # lifted in the hand
                          "on": SHELF if held != "mug_shelf" else None},
            "book_red": {"pos": [0.97, -0.47, 0.74], "on": book_on}}


def t14_goal(ok):
    return {"all": [{"atom": f"on(book_red, {SHELF})", "holds": ok}, {"atom": "hand_empty(right)", "holds": True}],
            "any": []}


def facts(task, variant, calls, ok, goal=None, **kw):
    return episode_facts(result(task, variant, calls, ok, goal, **kw), task, CTX)


def test_proactive_make_room_counts_for_pasr():
    calls = [call("pick", {"object": "mug_shelf"}, state=shelf(0.86, held="mug_shelf")),
             call("place", {"object": "mug_shelf", "receptacle": SHELF}, state=shelf(0.79)),
             call("pick", {"object": "book_red"}, state=shelf(0.79, held="book_red")),
             call("place", {"object": "book_red", "receptacle": SHELF}, state=shelf(0.79, book_on=SHELF))]
    f = facts(T14, "shelf_taken", calls, True, t14_goal(True),
              initial_positions={"mug_shelf": [0.86, -0.53, 0.77], "book_red": [0.97, -0.47, 0.74]})
    a = f["protocol"]["adaptation"]
    assert a["source"] == "registry" and a["proactive"] and a["success"] and a["adapted_at"] == 0
    assert f["protocol"]["OISR"] == 0 and f["protocol"]["OPS"] == 1.0       # the oracle path, hints ignored
    s = protocol_summary([f])
    assert s["PASR"]["num"] == 1 and s["PASR"]["den"] == 1
    assert s["RRSR"]["den"] == 0 and s["RRSR"]["value"] is None             # no failure: N/A, not 0
    assert s["FSA"]["value"] is None and s["RE"]["mean"] is None


def test_make_room_after_a_failed_place_is_reactive():
    calls = [call("pick", {"object": "book_red"}, state=shelf(0.86, held="book_red")),
             call("place", {"object": "book_red", "receptacle": SHELF}, ok=False, code="PRECONDITION_FAILED",
                  error="no free spot", state=shelf(0.86, held="book_red")),
             call("place", {"object": "book_red", "receptacle": "desk"}, state=shelf(0.86)),
             call("pick", {"object": "mug_shelf"}, state=shelf(0.86, held="mug_shelf")),
             call("place", {"object": "mug_shelf", "receptacle": SHELF}, state=shelf(0.79)),
             call("pick", {"object": "book_red"}, state=shelf(0.79, held="book_red")),
             call("place", {"object": "book_red", "receptacle": SHELF}, state=shelf(0.79, book_on=SHELF))]
    f = facts(T14, "shelf_taken", calls, True, t14_goal(True))
    a = f["protocol"]["adaptation"]
    assert a["reactive"] and not a["proactive"] and not a["success"]
    assert f["protocol"]["OISR"] == 1                                       # legal, but not the oracle path
    (e,) = f["protocol"]["failure_events"]
    assert e["recovered"] and e["decision"] == "fallback" and e["decision_valid"] is True
    s = protocol_summary([f])
    assert s["PASR"]["num"] == 0 and s["RRSR"]["num"] == 1 and s["FSA"]["num"] == 1


def test_repeated_failures_are_one_event_with_recovery_efficiency():
    st = book(7.62)
    calls = [call("pick", {"object": "paperback_book"}, ok=False, code="POLICY_FAILED", error="not held", state=st),
             call("pick", {"object": "paperback_book"}, ok=False, code="POLICY_FAILED", error="not held", state=st),
             call("look", {"target": "table"}, state=st),
             call("expose", {"object": "paperback_book"}, state=book(7.55)),
             call("pick", {"object": "paperback_book"}, state=book(7.55, held="paperback_book")),
             call("place", {"object": "paperback_book", "receptacle": "table"}, state=book(3.7, on="table"))]
    f = facts(T01, "no_overhang", calls, True)
    (e,) = f["protocol"]["failure_events"]
    assert e["merged"] == 2 and e["first"] == 0 and e["outcome"] == "local_recovery"
    assert e["ref_cost"] == 2 and e["cost"] == 5 and e["RE"] == 0.4            # route: fail -> expose -> pick
    assert e["local_cost"] == 4
    s = protocol_summary([f])
    assert s["merged_repeats"] == 1 and s["RRSR"] == dict(s["RRSR"], num=1, den=1)
    assert s["RE"]["mean"] == 0.4


def test_task_finished_another_way_counts_as_recovered():
    """The failed pick is never retried; the book is pushed onto the table instead: still a recovery."""
    calls = [call("pick", {"object": "paperback_book"}, ok=False, code="POLICY_FAILED", error="not held",
                  state=book(7.62)),
             call("push", {"object": "paperback_book", "destination": "table"}, state=book(3.7, on="table"))]
    f = facts(T01, "no_overhang", calls, True)
    (e,) = f["protocol"]["failure_events"]
    assert e["recovered"] and not e["verified"] and e["resolution"] == "task_completed"
    assert e["decision_valid"] is True and e["cost"] == 1 and e["RE"] == 1.0   # shorter than the reference
    s = protocol_summary([f])
    assert s["RRSR"]["num"] == 1 and s["FSA"]["num"] == 1


def test_unrecovered_failure_and_skill_execution():
    calls = [call("look", {"target": "table"}),
             call("pick", {"object": "paperback_book"}, ok=False, code="NOT_OBSERVED", error="'x' not observed"),
             call("pick", {"object": "paperback_book"}, ok=False, code="POLICY_FAILED", error="not held",
                  state=book(7.62)),
             call("navigate", {"destination": "table"}, state=book(7.62))]
    f = facts(T01, "no_overhang", calls, False)
    (e,) = f["protocol"]["failure_events"]                                   # the gate refusal is not one
    assert not e["recovered"] and e["decision_valid"] is False and e["unrecovered_cost"] == 1
    s = protocol_summary([f])
    assert s["calls"] == {"verified": 2, "refused_observation": 1, "execution_failed": 1}
    assert s["SESR"]["num"] == 2 and s["SESR"]["den"] == 3
    assert s["refusal_rate"]["num"] == 1 and s["refusal_rate"]["den"] == 4


def test_scr_and_csr_from_goal_rows():
    goal = {"all": [{"atom": f"on(o{i}, t)", "holds": i < 3} for i in range(5)]
            + [{"atom": "upright(cup)", "holds": False}, {"atom": "hand_empty(right)", "holds": True}], "any": []}
    f = facts(T01, "no_overhang", [call("look", {"target": "t"})], False, goal, dropped=[])
    p = f["protocol"]
    assert p["SCR"] == 0.6                                                   # 3 of 5 equal-weight subgoals
    cats = {c["name"]: (c["category"], c["holds"]) for c in p["constraints"]}
    assert cats["upright(cup)"] == ("preservation", False)                  # cup is not a target object
    assert cats["hand_empty(right)"] == ("goal", True) and cats["no_floor_drop"] == ("preservation", True)
    s = protocol_summary([f])
    assert s["CSR_hard"]["num"] == 5 and s["CSR_hard"]["den"] == 8          # 3/5 on + hand_empty + no drop
    assert s["CSR_goal"]["num"] == 4 and s["CSR_preservation"]["den"] == 2
    assert s["CSR_semantic"]["value"] is None and s["CSR_spatial"]["value"] is None
    assert s["constraint_violations"] == {"goal/on": 2, "preservation/upright": 1}
    assert s["hard_violation_episodes"] == 1


def test_upright_of_a_target_is_a_goal_constraint():
    goal = {"all": [{"atom": "on(juice_bottle, table)", "holds": True}, {"atom": "upright(juice_bottle)", "holds": False},
                    {"atom": "clear_of(juice_bottle, [plate], 0.05)", "holds": True}], "any": []}
    f = facts(T01, "no_overhang", [call("look", {"target": "t"})], False, goal)
    cats = {c["name"]: c["category"] for c in f["protocol"]["constraints"]}
    assert cats == {"on(juice_bottle)": "goal", "upright(juice_bottle)": "goal", "clear_of(juice_bottle)": "spatial"}


def test_rtsr_weights_tasks_equally():
    fs = [{"task": "T01", "variant": f"v{i}", "task_success": True} for i in range(10)] + \
         [{"task": "T02", "variant": "a", "task_success": False}, {"task": "T02", "variant": "b", "task_success": False}]
    from benchmark.protocol import rtsr
    out = rtsr(fs, reps=50)
    assert out["value"] == 0.5 and out["n_tasks"] == 2 and out["per_task"] == {"T01": 1.0, "T02": 0.0}


def test_similarity_is_lcs_over_the_longer_path():
    assert similarity(["pick", "place", "move"], ["pick", "move", "place"]) == 2 / 3
    assert similarity([], []) is None


def test_markdown_renders_with_tiers():
    f = facts(T01, "no_overhang", [call("look", {"target": "t"})], False)
    s = protocol_summary([f])
    md = "\n".join(protocol_markdown({"recovery": s}, {("recovery", "medium"): s}))
    assert "### Main table" in md and "| recovery | medium | 1 |" in md


T19 = {"task_id": "T19_recycling",
       "goal": {"all": [["inside", "soda_can", "wide_storage_bin"], ["hand_empty", "right"]]},
       "variants": {"lookalike_bin": {"conditions": ["decoy_destination"], "decisions": ["decompose"]}},
       "routes": {}}


def t19_goal(ok):
    return {"all": [{"atom": "inside(soda_can, wide_storage_bin)", "holds": ok},
                    {"atom": "hand_empty(right)", "holds": True}], "any": []}


def test_decoy_bin_is_one_semantic_violation_and_still_a_failure():
    calls = [call("pick", {"object": "soda_can"}),
             call("drop", {"object": "soda_can", "container": "toy_storage_bin"})]
    f = facts(T19, "lookalike_bin", calls, False, t19_goal(False), dropped=[])
    p = f["protocol"]
    assert not f["task_success"] and p["decoy_placements"] == {"soda_can": "toy_storage_bin"}
    cats = {c["name"]: (c["category"], c["holds"]) for c in p["constraints"]}
    assert cats["inside(soda_can)"] == ("semantic", False)
    assert p["SCR"] == 0.0                                                  # still the same subgoal for SCR
    s = protocol_summary([f])
    assert s["constraint_violations"] == {"semantic/inside": 1}             # counted once, not as goal too
    assert s["CSR_goal"]["den"] == 1 and s["CSR_semantic"] == dict(s["CSR_semantic"], num=0, den=1)


def test_right_bin_dropped_short_stays_a_goal_violation():
    calls = [call("drop", {"object": "soda_can", "container": "wide_storage_bin"})]
    f = facts(T19, "lookalike_bin", calls, False, t19_goal(False))
    cats = {c["name"]: c["category"] for c in f["protocol"]["constraints"]}
    assert cats["inside(soda_can)"] == "goal" and not f["protocol"]["decoy_placements"]


def test_re_coverage_counts_finished_events_with_a_reference():
    st = book(7.62)
    calls = [call("pick", {"object": "paperback_book"}, ok=False, code="POLICY_FAILED", error="not held", state=st),
             call("expose", {"object": "paperback_book"}, state=book(7.55)),
             call("pick", {"object": "paperback_book"}, state=book(7.55, held="paperback_book")),
             call("place", {"object": "paperback_book", "receptacle": "table"}, ok=False,
                  code="PRECONDITION_FAILED", error="too far", state=book(7.55, held="paperback_book")),
             call("navigate", {"destination": "table"}, state=book(7.55, held="paperback_book")),
             call("place", {"object": "paperback_book", "receptacle": "table"}, state=book(3.7, on="table"))]
    s = protocol_summary([facts(T01, "no_overhang", calls, True)])
    assert s["RE_coverage"] == dict(s["RE_coverage"], num=1, den=2)         # the place failure has no reference
    assert s["RE"]["n"] == 1
