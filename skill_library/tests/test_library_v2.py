"""Simulator-free checks of the verb-based SkillNode library."""

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from skill_library.check import SYNONYM_GROUPS, check_library  # noqa: E402
from skill_library.catalog import load_skills  # noqa: E402


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


def _contract(verb):
    contracts = json.loads((ROOT / "contract_library/skill_contracts.json").read_text())["contracts"]
    return next(c for c in contracts if c["verb"] == verb)


def test_pick_has_noun_selected_paths():
    paths = [p["path_id"] for p in _contract("pick")["policy_plan"]["paths"]]
    assert {"top_pinch", "round_rim", "handle", "flat_edge", "floor_top", "microwave_cavity"} <= set(paths)


def test_heat_has_microwave_and_stove_paths():
    assert [p["path_id"] for p in _contract("heat")["policy_plan"]["paths"]] == ["microwave", "stove_pot"]


def test_contracts_carry_no_relations_or_skill_pairing():
    contracts = json.loads((ROOT / "contract_library/skill_contracts.json").read_text())["contracts"]
    for c in contracts:
        assert "relations" not in c and "skill_id" not in c, c["verb"]



def test_skill_md_hides_policies_and_documents_the_call():
    for s in load_skills().values():
        md = (ROOT / "skill_library/skills" / s["skill_id"] / "SKILL.md").read_text()
        assert "policy_" not in md and "Verifier" not in md and "GT:" not in md, s["verb"]
        assert f'"contract": "{s["verb"]}"' in md, s["verb"]
