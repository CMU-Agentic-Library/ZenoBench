"""Skill System (v5): SKILL.md loading, schema validation, registry, tracks, executors, dispatch.

No simulator: the dispatch tests use a fake runner and fake predicates.

    python -m pytest -q skill_ext/tests
"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from skill_ext import SkillRegistry, SkillSchemaError, validate_spec  # noqa: E402
from skill_ext import dispatch as D  # noqa: E402
from skill_ext import predicates as P  # noqa: E402
from skill_ext.executors import PolicyExecutor  # noqa: E402
from skill_ext.schema import parse_atom  # noqa: E402

EXAMPLES = ROOT / "skill_ext/examples"


def write_skill(tmp, name, front, body="doc", files=None):
    d = tmp / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text("---\n" + textwrap.dedent(front).strip() + "\n---\n" + body + "\n")
    for fn, txt in (files or {}).items():
        (d / fn).write_text(textwrap.dedent(txt))
    return d


# ----------------------------------------------------------------- registry and tracks
def test_builtins_mirror_the_contract_library_unchanged():
    reg = SkillRegistry.default()
    doc = json.loads((ROOT / "contract_library/skill_contracts.json").read_text())
    assert reg.names("fixed") == sorted(c["verb"] for c in doc["contracts"])
    assert len(reg.names("fixed")) == 71
    pick = reg.get("pick", "fixed")
    assert pick.kind == "builtin" and pick.executor["type"] == "builtin"


def test_examples_load_and_only_join_the_open_track():
    reg = SkillRegistry.default()
    report = reg.load_dir(EXAMPLES)
    assert all(r["ok"] for r in report), report
    user = reg.names("open", kind="user")
    assert user == ["deliver", "raise_held", "rl_raise_held", "vla_raise_held"]
    assert not set(user) & set(reg.names("fixed"))
    with pytest.raises(KeyError):
        reg.get("deliver", "fixed")
    assert reg.fingerprint("fixed") != reg.fingerprint("open")
    assert reg.fingerprint("fixed") == SkillRegistry.default().fingerprint("fixed")


def test_menu_never_shows_the_executor():
    reg = SkillRegistry.default()
    reg.load_dir(EXAMPLES)
    for row in reg.menu("open"):
        blob = json.dumps(row)
        assert "executor" not in row and "policy.py" not in blob and "steps" not in row
    d = next(r for r in reg.menu("open") if r["name"] == "deliver")
    assert d["preconditions"] == ["hand_empty(hand=right)"]
    assert "on(object=$object, support=$support)" in d["effects"]


def test_dynamic_register_reload_unregister(tmp_path):
    reg = SkillRegistry.default()
    front = """
    name: tidy_one
    description: Put one object on a support, version {v}.
    parameters: {{object: {{type: object_ref, required: true}}, support: {{type: support_ref, required: true}}}}
    effects: ["on(object=$object, support=$support)"]
    executor: {{type: scripted, steps: [{{skill: pick, args: {{object: $object}}}}, {{skill: place, args: {{object: $object, support: $support}}}}]}}
    """
    d = write_skill(tmp_path, "tidy_one", front.format(v=1))
    s1 = reg.register(d)
    assert reg.has("tidy_one")
    (d / "SKILL.md").write_text("---\n" + textwrap.dedent(front.format(v=2)).strip() + "\n---\n")
    s2 = reg.reload("tidy_one")
    assert s2.sha1 != s1.sha1 and "version 2" in s2.description
    with pytest.raises(SkillSchemaError):
        reg.register(d)                                       # already registered, no replace
    reg.unregister("tidy_one")
    assert not reg.has("tidy_one")
    with pytest.raises(KeyError):
        reg.unregister("pick")                                # built-ins stay


# ----------------------------------------------------------------- schema validation
BAD = {
    "bad name": ("name: Bad-Name\ndescription: does things well\nparameters: {}\n"
                 "executor: {type: scripted, steps: [{skill: wait}]}", "does not match"),
    "builtin clash": ("name: pick\ndescription: my own pick skill\nparameters: {}\n"
                      "executor: {type: scripted, steps: [{skill: wait}]}", "built-in"),
    "unknown predicate": ("name: foo\ndescription: does things well\nparameters: {}\n"
                          "effects: ['levitating(object=x)']\nexecutor: {type: scripted, steps: [{skill: wait}]}",
                          "unknown predicate"),
    "undeclared param": ("name: foo\ndescription: does things well\nparameters: {}\n"
                         "effects: ['upright(object=$obj)']\nexecutor: {type: scripted, steps: [{skill: wait}]}",
                         "names no declared parameter"),
    "bad param type": ("name: foo\ndescription: does things well\nparameters: {x: {type: banana}}\n"
                       "executor: {type: scripted, steps: [{skill: wait}]}", "is not one of"),
    "unknown field": ("name: foo\ndescription: does things well\nparameters: {}\ncolour: red\n"
                      "executor: {type: scripted, steps: [{skill: wait}]}", "unknown field"),
    "policy without entry": ("name: foo\ndescription: does things well\nparameters: {}\nexecutor: {type: vla}",
                             "needs entry"),
    "missing entry file": ("name: foo\ndescription: does things well\nparameters: {}\n"
                           "executor: {type: rl, entry: nope.py:Policy}", "could not be loaded"),
    "scripted unknown skill": ("name: foo\ndescription: does things well\nparameters: {}\n"
                               "executor: {type: scripted, steps: [{skill: teleport}]}", "unknown skill"),
}


@pytest.mark.parametrize("case", sorted(BAD))
def test_schema_rejects(tmp_path, case):
    front, needle = BAD[case]
    reg = SkillRegistry.default()
    d = write_skill(tmp_path, "s", front)
    with pytest.raises(SkillSchemaError) as e:
        reg.load_dir(tmp_path)
    assert needle in str(e.value), str(e.value)


def test_cycle_between_user_skills_is_rejected(tmp_path):
    reg = SkillRegistry.default()
    for a, b in (("aa", "bb"), ("bb", "aa")):
        write_skill(tmp_path, a, f"name: {a}\ndescription: calls the other one\nparameters: {{}}\n"
                                 f"executor: {{type: scripted, steps: [{{skill: {b}}}]}}")
    with pytest.raises(SkillSchemaError, match="calls itself"):
        reg.load_dir(tmp_path)


def test_non_strict_load_reports_and_continues(tmp_path):
    reg = SkillRegistry.default()
    write_skill(tmp_path, "good", "name: good_one\ndescription: waits a moment\nparameters: {}\n"
                                  "executor: {type: scripted, steps: [{skill: wait}]}")
    write_skill(tmp_path, "zbad", "name: pick\ndescription: shadow a builtin\nparameters: {}\n"
                                  "executor: {type: scripted, steps: [{skill: wait}]}")
    rep = reg.load_dir(tmp_path, strict=False)
    assert [r["ok"] for r in rep] == [True, False]
    assert reg.has("good_one") and reg.get("pick").kind == "builtin"


def test_atom_parsing_forms():
    assert parse_atom("not on(object=$o, support=kitchen_island/top)") == \
        {"pred": "on", "args": {"object": "$o", "support": "kitchen_island/top"}, "negated": True}
    assert parse_atom("held_above(object=$o, height_m=0.05)")["args"]["height_m"] == 0.05
    assert parse_atom({"pred": "upright", "args": {"object": "mug"}})["negated"] is False
    with pytest.raises(ValueError):
        parse_atom("on object")
    assert validate_spec({"name": "ok_one", "description": "a valid skill", "parameters": {},
                          "executor": {"type": "scripted", "steps": [{"skill": "wait"}]}},
                         builtin_verbs={"wait"})["preconditions"] == []


# ----------------------------------------------------------------- dispatch (fake runner / predicates)
class FakeRig:
    def __init__(self):
        self.events, self.held, self.q_cmd = [], None, [0.0] * 7
        self.facts = {}

    def log(self, label, **kw):
        self.events.append((label, kw))

    def step(self, n=1):
        pass


class FakeRunner:
    """Built-in runner stand-in: records calls; ``fail`` names verbs that fail."""

    def __init__(self, rig, fail=()):
        from zeno_skills.skill_runtime import SkillResult
        self.SR, self.rig, self.fail, self.calls, self.trace = SkillResult, rig, set(fail), [], []

    def contract(self, key):
        if key not in {"pick", "place", "navigate", "wait"}:
            raise KeyError(key)
        return {"verb": key, "inputs": {}}

    def run(self, key, args, depth=0):
        self.contract(key)                                  # the real runner raises KeyError the same way
        self.calls.append((key, dict(args), depth))
        ok = key not in self.fail
        if ok and key == "place":
            self.rig.facts[("on", args["object"], args["support"])] = True
        if ok and key == "pick":
            self.rig.held = args["object"]
        if ok and key == "place":
            self.rig.held = None
        return self.SR(key, key, key, ok, "p", [], [], [], {}, {}, error=None if ok else "boom",
                       error_code=None if ok else "POLICY_FAILED")


def fake_predicates(monkeypatch):
    def pred(fn):
        return SimpleNamespace(evaluate=fn)
    table = {"on": pred(lambda rig, ctx, object, support: (rig.facts.get(("on", object, support), False), "")),
             "hand_empty": pred(lambda rig, ctx, hand: (rig.held is None, "")),
             "holding": pred(lambda rig, ctx, hand, object: (rig.held == object, ""))}
    monkeypatch.setattr(P, "predicate_table", lambda: table)
    monkeypatch.setattr(D, "evaluate_atoms", P.evaluate_atoms)
    import zeno_skills.skill_runtime as sr
    monkeypatch.setattr(sr, "before_snapshot", lambda rig: {})


def make_proxy(monkeypatch, fail=(), track="open"):
    fake_predicates(monkeypatch)
    rig = FakeRig()
    base = FakeRunner(rig, fail)
    reg = SkillRegistry.default()
    reg.load_dir(EXAMPLES)
    ep = SimpleNamespace(runner=base, task={"instruction": "tidy"}, observer=None)
    proxy = D.install(ep, reg, track)
    return proxy, base, rig


def test_builtins_pass_through_unchanged(monkeypatch):
    proxy, base, _ = make_proxy(monkeypatch)
    r = proxy.run("pick", {"object": "mug"})
    assert r.success and base.calls == [("pick", {"object": "mug"}, 0)]
    assert proxy.contract("pick") == {"verb": "pick", "inputs": {}}


def test_scripted_user_skill_runs_nested_calls_and_checks_effects(monkeypatch):
    proxy, base, rig = make_proxy(monkeypatch)
    r = proxy.run("deliver", {"object": "mug", "support": "shelf/top"})
    assert r.success, r.error
    assert [c[0] for c in base.calls] == ["navigate", "pick", "navigate", "place"]
    assert all(c[2] == 1 for c in base.calls)                       # nested depth
    assert [p["holds"] for p in r.postconditions] == [True, True]
    assert r.contract_id == "user:deliver"


def test_scripted_user_skill_stops_at_first_failure(monkeypatch):
    proxy, base, _ = make_proxy(monkeypatch, fail={"pick"})
    r = proxy.run("deliver", {"object": "mug", "support": "shelf/top"})
    assert not r.success and r.error_code == "SUBSKILL_FAILED"
    assert [c[0] for c in base.calls] == ["navigate", "pick"]
    assert r.children[-1]["success"] is False


def test_preconditions_refuse_before_acting(monkeypatch):
    proxy, base, rig = make_proxy(monkeypatch)
    rig.held = "spoon"
    r = proxy.run("deliver", {"object": "mug", "support": "shelf/top"})
    assert r.error_code == "PRECONDITION_FAILED" and base.calls == []


def test_fixed_track_does_not_know_user_skills(monkeypatch):
    proxy, base, _ = make_proxy(monkeypatch, track="fixed")
    with pytest.raises(KeyError):
        proxy.contract("deliver")
    with pytest.raises(KeyError):
        proxy.run("deliver", {"object": "mug", "support": "shelf/top"})


def test_missing_and_unknown_inputs(monkeypatch):
    from zeno_skills.skill_runtime import ContractError
    proxy, _, _ = make_proxy(monkeypatch)
    with pytest.raises(ContractError, match="missing input"):
        proxy.run("deliver", {"object": "mug"})
    with pytest.raises(ContractError, match="unknown inputs"):
        proxy.run("deliver", {"object": "mug", "support": "s", "speed": 3})


def test_policy_executors_loop_until_terminate():
    """raise_held / rl_raise_held / vla_raise_held (mock) on a fake context: TCP z integrates the actions."""
    reg = SkillRegistry.default()
    reg.load_dir(EXAMPLES)
    for name, dz_goal in (("raise_held", 0.06), ("rl_raise_held", 0.05), ("vla_raise_held", 0.045)):
        spec = reg.get(name)
        assert isinstance(spec.runner, PolicyExecutor)
        z = [0.9]

        class Ctx:
            instruction = "lift"

            def observe(self, fields, args):
                return {"proprio": {"tcp_pos": [0.0, 0.0, z[0]]}, "images": []}

            def act(self, space, action):
                assert space == "ee_delta" and max(abs(v) for v in action["ee_delta"]) <= 0.03 + 1e-9
                z[0] += action["ee_delta"][2]
                return {"ok": True}
        out = spec.runner.run(Ctx(), {"object": "mug", "height_m": 0.06})
        assert out.success and out.steps[-1].get("terminate"), (name, out.steps)
        assert abs((z[0] - 0.9) - dz_goal) < 0.012, (name, z[0] - 0.9)
