"""Simulator-free checks of the verb-based SkillNode library."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from skill_library.check import SYNONYM_GROUPS, check_library  # noqa: E402
from skill_library.graph import GraphValidationError, ground, load_skills, validate_subgraph  # noqa: E402


def test_exports_are_current_and_library_valid():
    out = subprocess.run([sys.executable, "tools/build_skill_library.py", "--check"], cwd=ROOT,
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr


def test_seventy_distinct_verbs_no_synonyms():
    skills = load_skills()
    verbs = [s["verb"] for s in skills.values()]
    assert len(verbs) == len(set(verbs)) == 70
    for group in SYNONYM_GROUPS:
        assert len(set(verbs) & group) <= 1, group


def test_every_policy_used_and_every_pre_post_is_a_registered_predicate():
    from zeno_skills.predicates import REGISTRY
    from zeno_skills.interface_ids import POLICY_PUBLIC_IDS
    contracts = json.loads((ROOT / "contract_library/skill_contracts.json").read_text())["contracts"]

    def walk(steps):
        for st in steps:
            if "foreach" in st:
                yield from walk(st["steps"])
            elif "policy" in st:
                yield st["policy"]
    used = {pid for c in contracts for p in c["policy_plan"]["paths"] for pid in walk(p["steps"])}
    from skill_library.check import RETIRED_POLICIES
    assert used == set(POLICY_PUBLIC_IDS.values()) - set(RETIRED_POLICIES)
    assert not used & set(RETIRED_POLICIES)
    for c in contracts:
        for atom in c["requires"] + c["ensures"]:
            assert atom["pred"] in REGISTRY
        for v in c["verifier"]:
            assert v["gt_sources"]


def test_relations_have_previous_next_and_fallback_or_alternative():
    skills = load_skills()
    for s in skills.values():
        rel = s["relations"]
        assert rel["previous"] or rel["next"], s["verb"]
        assert rel["fallback"] or rel["fallback_for"] or rel["alternative"], s["verb"]


def test_pick_has_noun_selected_paths_and_expose_repairs_it():
    pick = next(s for s in load_skills().values() if s["verb"] == "pick")
    paths = [p["path_id"] for p in pick["policy_paths"]]
    assert {"top_pinch", "round_rim", "handle", "flat_edge", "floor_top", "microwave_cavity"} <= set(paths)
    fb = {r["verb"]: r for r in pick["relations"]["fallback"]}
    assert fb["expose"]["type"] == "repair" and fb["expose"]["repairs"] == "edge_overhang"


def test_heat_has_microwave_and_stove_paths_with_stove_alternative():
    heat = next(s for s in load_skills().values() if s["verb"] == "heat")
    assert [p["path_id"] for p in heat["policy_paths"]] == ["microwave", "stove_pot"]
    alt = [r for r in heat["relations"]["alternative"] if r["verb"] == "heat"]
    assert alt and alt[0]["bind"]["appliance"] == "kitchen_stove"


def test_subgraph_with_output_reference_validates_and_grounds():
    graph = {"schema_version": 2, "kind": "skill_subgraph", "subgoal_id": "find_and_go", "nodes": [
        {"id": "n1", "skill": "search", "args": {"object": {"ref": "the lid"}}, "depends_on": []},
        {"id": "n2", "skill": "navigate", "args": {"destination": {"from": "n1.found_on"}}, "depends_on": ["n1"]},
        {"id": "n3", "skill": "uncover", "args": {"container": {"ref": "the pot"}}, "depends_on": ["n2"]}]}
    order = validate_subgraph(graph)
    assert [n["id"] for n in order] == ["n1", "n2", "n3"]
    ann = json.loads((ROOT / "tasks/kitchen_skills/annotation.json").read_text())
    calls = ground(graph, {"the lid": "pot_lid", "the pot": "handled_cooking_pot"}, ann)
    assert calls[1]["args"]["destination"] == {"from": "n1.found_on"}
    bad = json.loads(json.dumps(graph))
    bad["nodes"][1]["args"]["destination"] = {"from": "n3.lid"}
    with pytest.raises(GraphValidationError):
        validate_subgraph(bad)


def test_planner_decomposes_tasks_into_skill_chains():
    from skill_library.planner import solve_task
    catalog = json.loads((ROOT / "skill_library/tasks.json").read_text())
    tasks = {t["id"]: t for t in catalog["tasks"]}
    for tid in ("collect_fruits", "throw_away_can", "flip_book"):
        steps, _, _ = solve_task(tasks[tid], atomic_only=not tasks[tid].get("composite"))
        assert steps, tid
    verbs = [sk["verb"] for sk, _, _ in solve_task(tasks["flip_book"])[0]]
    assert verbs[-1] == "flip"
