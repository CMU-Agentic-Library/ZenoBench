"""Permission checks of the observation-limited interface (no simulator).

A stub rig over the real kitchen_skills annotation: object poses come from the
annotation, visibility is decided by the test (``rig.visible``), and every
policy entry is replaced by a tripwire so a refused call provably moves
nothing.  The in-simulator counterpart is benchmark/tests/sim_permissions.py.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from zeno_skills.annotations import SceneAnnotations
from zeno_skills.evaluator import Geometry

ROOT = Path(__file__).resolve().parents[2]
ANN = ROOT / "tasks/kitchen_skills/annotation.json"


class StubRig:
    def __init__(self):
        self.ann = SceneAnnotations(ANN)
        self.geo = Geometry(self.ann)
        self.held = None
        self.left_held = None
        self.tick = 0
        self.events = []
        self.memory = {"observed": {}, "wiped": {}, "stirred": {}, "explored": {}, "initial_support": {}}
        self.thermal = None
        self.caption = ""
        self.visible = set()
        self.poses = {n: (np.asarray(o["position"], float), np.array([1.0, 0, 0, 0])) for n, o in self.ann.objects.items()}
        self.moves = 0

    def state(self):
        return {"objects": {n: {"pos": p.tolist(), "quat": q.tolist()} for n, (p, q) in self.poses.items()},
                "joints": {}, "temperatures_c": {}}

    def obj_pose(self, n):
        return self.poses[n]

    def base_pose(self):
        return (7.5, 1.0, 0.0)

    def log(self, label, **kw):
        self.events.append((label, kw))

    def step(self, n=1):
        self.tick += n


@pytest.fixture
def gated(monkeypatch):
    from benchmark import observation as ob
    from episode.profile import apply_rig_flags, load_profile
    rig = StubRig()
    apply_rig_flags(rig, load_profile("benchmark"))
    obs = ob.Observer(rig)
    monkeypatch.setattr(ob.Observer, "visible", lambda self, name, st=None: name in self.rig.visible)
    monkeypatch.setattr(ob.Observer, "glance", lambda self, name, tag=None, image=False: self.snapshot(tag, image))
    runner = ob.GatedRunner(rig, obs, capture_images=False)
    # tripwire: any contract that gets past the gate tries to bind nouns / run policies
    from zeno_skills import skill_runtime as sr

    def tripwire(self, key, args, depth=0):
        rig.moves += 1          # the call got past the gate (would bind nouns and move)
        return sr.SkillResult("c", "s", key, False, None, [], [], [], {}, {}, error="TRIPWIRE", error_code="TRIPWIRE")
    monkeypatch.setattr(sr.SkillContractRunner, "run", tripwire)
    return rig, obs, runner


def test_hidden_and_nonexistent_objects_get_the_same_refusal(gated):
    rig, obs, runner = gated
    hidden = "bowl_inside_kitchen_cabinet"          # exists, never seen
    for verb, slot in (("pick", "object"), ("navigate", "destination"), ("fetch", "object"),
                       ("look", "target"), ("identify", "object"), ("heat", "food")):
        args = {slot: hidden}
        if verb == "fetch":
            args["receptacle"] = "kitchen_island/top"
        if verb == "heat":
            args["appliance"] = "kitchen_stove"
        a = runner.feedback(runner.run(verb, dict(args)), args)
        b_args = dict(args, **{slot: "golden_teapot"})
        b = runner.feedback(runner.run(verb, dict(b_args)), b_args)
        assert not a["success"] and not b["success"]
        assert a["error_code"] == b["error_code"] == "NOT_OBSERVED"
        assert a["error"].replace(hidden, "X") == b["error"].replace("golden_teapot", "X")
    assert rig.moves == 0


def test_composite_and_list_arguments_are_checked(gated):
    rig, obs, runner = gated
    rig.visible = {"wooden_block_a"}
    obs.snapshot()
    res = runner.run("collect", {"objects": ["wooden_block_a", "bowl_inside_kitchen_cabinet"], "container": "trash_can"})
    assert res.error_code == "NOT_OBSERVED"
    res = runner.run("sweep", {"objects": ["wooden_block_a", "golden_teapot"], "radius_m": 0.05})
    assert res.error_code == "NOT_OBSERVED"
    assert rig.moves == 0


def test_contact_needs_current_view_or_hand(gated):
    rig, obs, runner = gated
    rig.visible = {"wooden_block_a"}
    obs.snapshot()                       # seen once ...
    rig.visible = set()
    obs.snapshot()                       # ... then out of view
    assert obs.known("wooden_block_a") and not obs.fresh("wooden_block_a")
    res = runner.run("pick", {"object": "wooden_block_a"})
    assert res.error_code == "NOT_IN_VIEW"
    res = runner.run("push", {"object": "wooden_block_a", "direction_xy": [1.0, 0.0], "distance_m": 0.1})
    assert res.error_code == "NOT_IN_VIEW"
    # navigation toward the remembered position is allowed (it reaches the runner)
    runner.run("navigate", {"destination": "wooden_block_a"})
    assert rig.moves == 1
    # an object in the hand is always available
    rig.held = {"name": "wooden_block_a"}
    rig.moves = 0
    runner.run("lift", {"object": "wooden_block_a", "height_m": 0.95})
    assert rig.moves == 1


def test_stale_cache_drives_to_the_remembered_pose(gated, monkeypatch):
    rig, obs, runner = gated
    rig.visible = {"soda_can"}
    obs.snapshot()
    old = list(obs.cache["soda_can"]["pos"])
    rig.visible = set()
    obs.snapshot()
    p, q = rig.poses["soda_can"]
    rig.poses["soda_can"] = (p + np.array([0.0, -1.2, 0.0]), q)     # moved while unobserved
    assert obs.stale("soda_can")
    seen = {}
    from zeno_skills import skill_runtime as sr

    def run(self, key, args, depth=0):
        seen["pos"] = rig.state()["objects"]["soda_can"]["pos"]
        return sr.SkillResult("c", "s", key, False, None, [], [], [], {}, {}, error="TRIPWIRE", error_code="TRIPWIRE")
    monkeypatch.setattr(sr.SkillContractRunner, "run", run)
    runner.run("navigate", {"destination": "soda_can"})
    assert np.allclose(seen["pos"], old)                       # the planner's belief, not GT
    assert not np.allclose(rig.state()["objects"]["soda_can"]["pos"], old)   # GT restored afterwards


def test_feedback_masks_unobserved_names(gated):
    rig, obs, runner = gated
    rig.visible = {"wooden_block_a"}
    obs.snapshot()
    from zeno_skills.skill_runtime import SkillResult
    res = SkillResult("c", "s", "clear_support(support=kitchen_island/top)", False, "p",
                      [{"atom": "support_clear(support=kitchen_island/top)", "holds": False,
                        "detail": "objects ['wooden_block_a', 'juice_bottle']"}], [], [], {"moved": ["juice_bottle"]}, {},
                      error="SUBSKILL_FAILED: pick_object(object=juice_bottle): x", error_code="SUBSKILL_FAILED")
    fb = runner.feedback(res, {"support": "kitchen_island/top"})
    text = json.dumps(fb)
    assert "juice_bottle" not in text and "wooden_block_a" in text and "<unobserved>" in text
    assert "recovery" not in fb and "bound_nouns" not in fb


def test_unknown_place_names_are_refused(gated):
    rig, obs, runner = gated
    res = runner.run("navigate", {"destination": "secret_room"})
    assert res.error_code == "NOT_OBSERVED"
    runner.run("navigate", {"destination": "kitchen_island/top"})      # static layout is known
    assert rig.moves == 1


def test_no_automatic_recovery_configuration(gated):
    rig, obs, runner = gated
    assert runner.auto_repair is False
    assert {"grasp_clearance", "edge_overhang"} <= runner.advisory
    assert "policy_045" in runner.skip_steps[("pick", "flat_edge")]
    assert rig.auto_recovery is False and rig.occlusion is True and rig.static_explore is True


def test_ungated_runner_refuses_nothing_but_keeps_the_cache(gated, monkeypatch):
    rig, obs, _ = gated
    from benchmark import observation as ob
    runner = ob.GatedRunner(rig, obs, gate=False, capture_images=False)
    res = runner.run("pick", {"object": "bowl_inside_kitchen_cabinet"})      # never seen: no refusal
    assert res.error_code == "TRIPWIRE" and rig.moves == 1
    assert obs.gated is False and runner.calls[-1]["verb"] == "pick"
