"""Failure injection (v5): spec validation, deterministic triggers, effects, hidden state.

No simulator: a fake rig records grip / teleport / joint calls; the real effects run in Isaac Sim
(benchmark/v5/validate.py --physics).

    python -m pytest -q failure_injection/tests
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from failure_injection import FailureSpecError, category, validate  # noqa: E402
from failure_injection import runtime as R  # noqa: E402
from failure_injection.spec import public_view_is_clean, seeded  # noqa: E402

ANN = json.loads((ROOT / "tasks/kitchen_skills/annotation.json").read_text())
OBJ = {o["name"] for o in ANN["objects"]}
ART = {a["name"] for a in ANN["articulated"]}
SUP = {s["name"] for s in ANN["supports"]}


def V(f):
    return validate(f, objects=OBJ, articulated=ART, supports=SUP)


# ----------------------------------------------------------------- validation
def test_valid_specs_of_every_kind():
    V([{"id": "g", "kind": "grasp", "trigger": {"skill": "pick", "args": {"object": "mug"}}},
       {"id": "s", "kind": "slip", "trigger": {"skill": "navigate", "while_holding": "mug"}},
       {"id": "p", "kind": "placement", "mode": "tipped", "trigger": {"skill": "place", "args": {"object": "mug"}},
        "report": [["upright", "mug"]]},
       {"id": "i", "kind": "ik", "trigger": {"skill": "pick", "args": {"object": "mug"}, "nth": 1}},
       {"id": "c", "kind": "capacity", "when": "initial", "check": [["count_inside_at_most", "storage_bin", 0]]},
       {"id": "d", "kind": "destination", "when": "dynamic", "trigger": {"skill": "pick"},
        "event": {"type": "move_object", "object": "oatmeal", "to": {"support": "dining_table_2/top", "xy": [3.5, 6.0]}}},
       {"id": "r", "kind": "resource", "when": "dynamic", "trigger": {"skill": "navigate"}, "after_fired": "g",
        "event": {"type": "into", "object": "wooden_block_a", "container": "mug"}},
       {"id": "k", "kind": "dependency", "when": "dynamic", "trigger": {"skill": "open"},
        "event": {"type": "set_joint", "articulated": "kitchen_microwave", "value": "closed"}}])


@pytest.mark.parametrize("bad,needle", [
    ([{"id": "a", "kind": "teleport"}], "kind"),
    ([{"id": "a", "kind": "grasp", "trigger": {"skill": "place"}}], "attaches to"),
    ([{"id": "a", "kind": "slip", "trigger": {"skill": "navigate"}}], "while_holding"),
    ([{"id": "a", "kind": "placement", "mode": "tipped", "trigger": {"skill": "place"}}], "report"),
    ([{"id": "a", "kind": "placement", "mode": "displaced", "trigger": {"skill": "place"}, "report": [["on", "x", "y"]],
       "to": {"support": "moon/top", "xy": [0, 0]}}], "unknown support"),
    ([{"id": "a", "kind": "capacity", "when": "initial"}], "check atoms"),
    ([{"id": "a", "kind": "dependency", "when": "dynamic", "trigger": {"skill": "open"},
       "event": {"type": "set_joint", "articulated": "garage", "value": "closed"}}], "unknown articulated"),
    ([{"id": "a", "kind": "grasp", "trigger": {"skill": "pick"}}, {"id": "a", "kind": "ik", "trigger": {"skill": "pick"}}],
     "unique id"),
    ([{"id": "a", "kind": "grasp", "trigger": {"skill": "pick"}, "after_fired": "zz"}], "after_fired"),
])
def test_invalid_specs(bad, needle):
    with pytest.raises(FailureSpecError, match=needle):
        V(bad)


def test_categories():
    act = {"id": "g", "kind": "grasp", "trigger": {"skill": "pick"}}
    ini = {"id": "c", "kind": "capacity", "when": "initial", "check": [["upright", "mug"]]}
    dyn = {"id": "d", "kind": "destination", "when": "dynamic", "trigger": {"skill": "pick"},
           "event": {"type": "move_object", "object": "oatmeal", "to": {"support": "dining_table_2/top", "xy": [3.5, 6]}}}
    assert category([act]) == {"action"}
    assert category([ini]) == {"task"}
    assert category([act, ini]) == {"action", "task", "mixed"}
    assert category([dyn]) == {"task", "dynamic"}


def test_seeded_values_are_reproducible_and_seed_dependent():
    f = {"id": "p", "jitter": {"xy": 0.03}}
    a = [seeded(f, "T", "v", s)["dxy"] for s in range(10, 20)]
    assert a == [seeded(f, "T", "v", s)["dxy"] for s in range(10, 20)]
    assert len({tuple(x) for x in a}) > 1 and all(abs(v) <= 0.03 + 1e-9 for x in a for v in x)


# ----------------------------------------------------------------- runtime on a fake rig
class FakeBody:
    def __init__(self, rig, name):
        self.rig, self.name = rig, name

    def set_world_pose(self, p, q):
        self.rig.poses[self.name] = (np.asarray(p, float), np.asarray(q, float))
        self.rig.teleports.append(self.name)

    def set_linear_velocity(self, v):
        pass

    set_angular_velocity = set_linear_velocity


class FakeArt:
    def __init__(self, rig, name):
        self.rig, self.name = rig, name

    def set_joint_positions(self, v, joint_indices):
        self.rig.joints[self.name] = float(v[0])

    def set_joint_velocities(self, v, joint_indices):
        pass


class FakeRig:
    def __init__(self):
        self.torch = SimpleNamespace(tensor=lambda x, dtype=None: np.asarray(x, float), zeros=np.zeros, float32=None)
        self.events, self.teleports, self.grips, self.tick = [], [], [], 0
        self.held = None
        self.base = [1.0, 1.0, 0.0]
        self.poses = {n: (np.array([1.0, 1.0, 0.9]), np.array([1.0, 0, 0, 0])) for n in ("mug", "oatmeal", "storage_bin")}
        self.joints = {"kitchen_microwave": -1.4}
        assets = {"mug": {"size": [0.09, 0.09, 0.12], "origin_to_bottom_center": [0, 0, -0.06]},
                  "oatmeal": {"size": [0.1, 0.1, 0.1], "origin_to_bottom_center": [0, 0, -0.05]},
                  "storage_bin": {"size": [0.3, 0.2, 0.15], "origin_to_bottom_center": [0, 0, 0]}}
        self.ann = SimpleNamespace(supports=[{"name": "dining_table_2/top", "z": 0.75}],
                                   articulated=[{"name": "kitchen_microwave", "closed_q": 0.0, "open_q": -1.4}],
                                   objects={n: {"asset": n} for n in assets}, asset_of=lambda o: assets[o["asset"]])
        self._bodies = {n: FakeBody(self, n) for n in self.poses}
        self._arts = {"kitchen_microwave": FakeArt(self, "kitchen_microwave")}
        self._dof = {"kitchen_microwave": 0}
        self.geo = SimpleNamespace(support_under=lambda n, st: {"name": "kitchen_island/top"},
                                   centre=lambda n, st: self.poses[n][0], bottom=lambda n, st: self.poses[n][0] - [0, 0, 0.05])

    def log(self, label, **kw):
        self.events.append((label, kw))

    def step(self, n=1):
        self.tick += n

    def grip(self, w, steps=100):
        self.grips.append(w)

    def obj_pose(self, n):
        return self.poses[n]

    def base_pose(self):
        return tuple(self.base)

    def state(self):
        return {"objects": {n: {"pos": p.tolist(), "quat": q.tolist()} for n, (p, q) in self.poses.items()}}

    def joint(self, n):
        return self.joints[n]


class FakeBase:
    CONTRACTS = {"pick": ["object"], "place": ["object", "support"], "navigate": ["destination"],
                 "approach": ["target"], "open": ["articulated"], "retreat": []}

    def __init__(self, rig):
        from zeno_skills.skill_runtime import SkillResult
        self.SR, self.rig, self.trace, self.calls = SkillResult, rig, [], []

    def contract(self, key):
        return {"verb": key, "contract_id": f"c_{key}", "skill_id": f"s_{key}",
                "action_predicate": {"name": key, "arguments": self.CONTRACTS[key]}}

    def run(self, key, args, depth=0):
        self.calls.append(key)
        if key == "pick":
            self.rig.held = {"name": args["object"]}
        if key == "place":
            self.rig.held = None
        if key in ("navigate", "approach", "retreat"):
            self.rig.base[0] += 0.5
        return self.SR(key, key, key, True, "p", [], [{"atom": f"holding(hand=right, object={args.get('object')})",
                                                       "holds": True, "detail": ""}] if key == "pick" else [],
                       [], {"x": 1}, {})


def make(failures, monkeypatch, atoms=None):
    rig = FakeRig()
    base = FakeBase(rig)
    monkeypatch.setattr(R.FailureRunner, "_atoms", lambda self, a: atoms(a) if atoms else
                        [{"atom": str(x), "holds": True, "detail": ""} for x in a])
    monkeypatch.setattr(R.FailureRunner, "_support_of", lambda self, n: "kitchen_island/top")
    cfg = {"task_id": "T", "variant": "v", "seed": 10}
    inj = R.FailureRunner(base, rig, failures, cfg)
    inj._supports = {"dining_table_2/top": {"z": 0.75}}
    return inj, base, rig


def test_grasp_fires_on_nth_pick_only(monkeypatch):
    inj, base, rig = make([{"id": "g", "kind": "grasp", "trigger": {"skill": "pick", "args": {"object": "mug"}, "nth": 2}}],
                          monkeypatch)
    r1 = inj.run("pick", {"object": "mug"})
    assert r1.success
    inj.run("place", {"object": "mug", "support": "dining_table_2/top"})
    r2 = inj.run("pick", {"object": "mug"})
    assert not r2.success and r2.error_code == "POLICY_FAILED" and "not held" in r2.error
    assert r2.postconditions[0]["holds"] is False and rig.held is None and rig.grips[-1] == R.RELEASE_W
    r3 = inj.run("pick", {"object": "mug"})
    assert r3.success                                       # fires once: the retry works
    assert inj.summary()["manifested"] == ["g"]


def test_slip_releases_before_driving(monkeypatch):
    inj, base, rig = make([{"id": "s", "kind": "slip", "trigger": {"skill": "navigate", "while_holding": "mug"}}], monkeypatch)
    inj.run("navigate", {"destination": "kitchen_island/top"})          # empty hand: not counted
    inj.run("pick", {"object": "mug"})
    x0 = rig.base[0]
    r = inj.run("navigate", {"destination": "dining_table_2/top"})
    assert not r.success and "slipped out of the hand" in r.error and rig.held is None
    assert rig.base[0] == x0 and base.calls.count("navigate") == 1     # the base never moved
    assert inj.counts["s"] == 1


def test_ik_blocks_until_base_reparked(monkeypatch):
    inj, base, rig = make([{"id": "i", "kind": "ik", "trigger": {"skill": "pick", "args": {"object": "mug"}}}], monkeypatch)
    assert "no IK solution" in inj.run("pick", {"object": "mug"}).error
    assert "no IK solution" in inj.run("pick", {"object": "mug"}).error        # same park: still refused
    assert base.calls == []
    inj.run("approach", {"target": "mug"})
    assert inj.run("pick", {"object": "mug"}).success
    assert base.calls == ["approach", "pick"]


def test_placement_reports_only_when_it_manifests(monkeypatch):
    f = {"id": "p", "kind": "placement", "mode": "displaced", "trigger": {"skill": "place", "args": {"object": "mug"}},
         "to": {"support": "dining_table_2/top", "xy": [3.5, 6.0]}, "report": [["inside", "mug", "storage_bin"]]}
    inj, base, rig = make([f], monkeypatch, atoms=lambda a: [{"atom": "inside(mug, storage_bin)", "holds": False,
                                                             "detail": "beside it"}])
    inj.run("pick", {"object": "mug"})
    r = inj.run("place", {"object": "mug", "support": "dining_table_2/top"})
    assert not r.success and r.error_code == "POSTCONDITION_FAILED" and "inside(mug, storage_bin) is false" in r.error
    assert rig.teleports == ["mug"] and abs(rig.poses["mug"][0][0] - 3.5) < 1e-6
    inj2, _, _ = make([f], monkeypatch)                    # report atoms still hold: not manifested, success kept
    inj2.run("pick", {"object": "mug"})
    assert inj2.run("place", {"object": "mug", "support": "dining_table_2/top"}).success
    assert inj2.summary()["fired"] == ["p"] and inj2.summary()["manifested"] == []


def test_tipped_placement_turns_the_object_on_its_side(monkeypatch):
    f = {"id": "p", "kind": "placement", "mode": "tipped", "trigger": {"skill": "place"}, "report": [["upright", "mug"]]}
    inj, _, rig = make([f], monkeypatch, atoms=lambda a: [{"atom": "upright(mug)", "holds": False, "detail": "90 deg"}])
    inj.run("pick", {"object": "mug"})
    r = inj.run("place", {"object": "mug", "support": "dining_table_2/top"})
    q = rig.poses["mug"][1]
    up_z = 1 - 2 * (q[1] ** 2 + q[2] ** 2)                 # R[2,2] of the new orientation
    assert not r.success and abs(up_z) < 1e-6


def test_dynamic_events_and_coupling(monkeypatch):
    fs = [{"id": "g", "kind": "grasp", "trigger": {"skill": "pick", "args": {"object": "mug"}}},
          {"id": "d", "kind": "destination", "when": "dynamic", "after_fired": "g", "trigger": {"skill": "pick"},
           "event": {"type": "move_object", "object": "oatmeal", "to": {"support": "dining_table_2/top", "xy": [3.5, 6.0]}}},
          {"id": "k", "kind": "dependency", "when": "dynamic", "trigger": {"skill": "open", "args": {"articulated": "kitchen_microwave"}},
           "event": {"type": "set_joint", "articulated": "kitchen_microwave", "value": "closed"}}]
    inj, base, rig = make(fs, monkeypatch)
    inj.run("pick", {"object": "mug"})                     # grasp fails -> d may fire from the next successful pick on
    assert "d" not in inj.fired                            # same call: the grasp failure made the pick unsuccessful
    inj.run("pick", {"object": "mug"})
    assert inj.fired["d"]["manifested"] and rig.teleports == ["oatmeal"]
    inj.run("open", {"articulated": "kitchen_microwave"})
    assert rig.joints["kitchen_microwave"] == 0.0 and inj.fired["k"]["value"] == 0.0
    assert [r["id"] for r in inj.failure_log] == ["g", "d", "k"]


def test_dynamic_move_skips_an_object_in_hand(monkeypatch):
    fs = [{"id": "d", "kind": "resource", "when": "dynamic", "trigger": {"skill": "pick"},
           "event": {"type": "move_object", "object": "mug", "to": {"support": "dining_table_2/top", "xy": [3.5, 6.0]}}}]
    inj, _, rig = make(fs, monkeypatch)
    inj.run("pick", {"object": "mug"})
    assert inj.fired["d"]["manifested"] is False and rig.teleports == []


def test_same_calls_same_failures(monkeypatch):
    fs = [{"id": "g", "kind": "grasp", "trigger": {"skill": "pick", "nth": 2}},
          {"id": "s", "kind": "slip", "trigger": {"skill": "navigate", "while_holding": "mug"}}]
    seqs = []
    for _ in range(2):
        inj, _, _ = make(fs, monkeypatch)
        out = []
        for k, a in [("pick", {"object": "mug"}), ("navigate", {"destination": "x"}), ("pick", {"object": "mug"}),
                     ("pick", {"object": "mug"}), ("navigate", {"destination": "x"})]:
            out.append(inj.run(k, a).success)
        seqs.append((out, [(r["id"], r["call_index"]) for r in inj.failure_log]))
    assert seqs[0] == seqs[1] == ([True, False, False, True, True], [("s", 2), ("g", 3)])


def test_failures_never_reach_the_planner():
    """public_task and the config-derived planner views carry no failure field."""
    from episode.catalog import public_task
    task = {"task_id": "T", "instruction": "do it", "variants": {"v": {"failures": [{"id": "g", "kind": "grasp"}]}}}
    assert public_view_is_clean(public_task(task, "v"))
    from episode.episode import public_result
    res = SimpleNamespace(success=False, error_code="POLICY_FAILED", error="pick_lift: mug not held (lift 0.000 m)",
                          preconditions=[], postconditions=[], outputs={}, children=[])
    assert public_view_is_clean(public_result({"contract": "pick", "args": {"object": "mug"}}, res))


def test_persistent_failures_fire_every_time(monkeypatch):
    fs = [{"id": "g", "kind": "grasp", "persist": True, "trigger": {"skill": "pick", "args": {"object": "mug"}}},
          {"id": "i", "kind": "ik", "persist": True, "until": "never",
           "trigger": {"skill": "place", "args": {"object": "oatmeal"}}}]
    inj, base, rig = make(fs, monkeypatch)
    assert not inj.run("pick", {"object": "mug"}).success
    assert not inj.run("pick", {"object": "mug"}).success          # the cup cannot be held: switch object
    assert inj.run("pick", {"object": "oatmeal"}).success
    assert "no IK" in inj.run("place", {"object": "oatmeal", "support": "dining_table_2/top"}).error
    inj.run("approach", {"target": "dining_table_2/top"})
    assert "no IK" in inj.run("place", {"object": "oatmeal", "support": "dining_table_2/top"}).error   # re-park does not help
    assert [r["id"] for r in inj.failure_log].count("g") == 2 and inj.summary()["manifested"] == ["g", "i"]


def test_persistent_ik_pinned_destination_leaves_the_substitute_free(monkeypatch):
    # the basket is out of reach from every park; the same apple's place on the tray must still work
    fs = [{"id": "i", "kind": "ik", "persist": True, "until": "never",
           "trigger": {"skill": "place", "args": {"object": "mug", "support": "storage_bin"}}}]
    inj, base, rig = make(fs, monkeypatch)
    inj.run("pick", {"object": "mug"})
    assert "no IK" in inj.run("place", {"object": "mug", "support": "storage_bin"}).error
    inj.run("approach", {"target": "storage_bin"})
    assert "no IK" in inj.run("place", {"object": "mug", "support": "storage_bin"}).error
    assert inj.run("place", {"object": "mug", "support": "dining_table_2/top"}).success


def test_until_moved_ends_when_the_neighbour_is_moved(monkeypatch):
    fs = [{"id": "g", "kind": "grasp", "persist": True, "until_moved": "oatmeal",
           "trigger": {"skill": "pick", "args": {"object": "mug"}}}]
    inj, base, rig = make(fs, monkeypatch)
    inj.check_initial()
    assert not inj.run("pick", {"object": "mug"}).success
    assert not inj.run("pick", {"object": "mug"}).success          # boxed in: retrying does not help
    rig.poses["oatmeal"] = (rig.poses["oatmeal"][0] + [0.02, 0, 0], rig.poses["oatmeal"][1])
    assert not inj.run("pick", {"object": "mug"}).success          # nudged 2 cm: still in the way
    rig.poses["oatmeal"] = (rig.poses["oatmeal"][0] + [0.1, 0, 0], rig.poses["oatmeal"][1])
    assert inj.run("pick", {"object": "mug"}).success              # moved away: the slot is free


def test_until_moved_ik_block_clears(monkeypatch):
    fs = [{"id": "i", "kind": "ik", "persist": True, "until": "never", "until_moved": "oatmeal",
           "trigger": {"skill": "pick", "args": {"object": "mug"}}}]
    inj, base, rig = make(fs, monkeypatch)
    inj.check_initial()
    assert "no IK" in inj.run("pick", {"object": "mug"}).error
    inj.run("approach", {"target": "mug"})
    assert "no IK" in inj.run("pick", {"object": "mug"}).error
    rig.poses["oatmeal"] = (rig.poses["oatmeal"][0] + [0.2, 0, 0], rig.poses["oatmeal"][1])
    assert inj.run("pick", {"object": "mug"}).success


def test_persistent_one_handed_slip_spares_a_two_handed_carry(monkeypatch):
    fs = [{"id": "s", "kind": "slip", "persist": True,
           "trigger": {"skill": "navigate", "while_holding": "mug", "one_handed": True}}]
    inj, base, rig = make(fs, monkeypatch)
    rig.left_held = None
    inj.run("pick", {"object": "mug"})
    assert "slipped" in inj.run("navigate", {"destination": "a"}).error
    inj.run("pick", {"object": "mug"})
    assert "slipped" in inj.run("navigate", {"destination": "a"}).error   # every one-handed carry
    inj.run("pick", {"object": "mug"})
    rig.left_held = {"name": "mug"}                                      # steadied with the left hand
    assert inj.run("navigate", {"destination": "a"}).success


@pytest.mark.parametrize("bad, needle", [
    ({"id": "x", "kind": "dependency", "persist": True, "check": [["on", "mug", "t"]]},
     "only grasp, slip, placement and ik"),
    ({"id": "x", "kind": "grasp", "until_moved": "oatmeal", "trigger": {"skill": "pick", "args": {"object": "mug"}}},
     "until_moved needs a persistent"),
    ({"id": "x", "kind": "grasp", "trigger": {"skill": "pick", "one_handed": True}}, "one_handed applies"),
])
def test_invalid_persistence_specs(bad, needle):
    with pytest.raises(FailureSpecError, match=needle):
        validate([bad])


def test_persistent_placement_displaces_every_time(monkeypatch):
    f = {"id": "p", "kind": "placement", "mode": "displaced", "persist": True,
         "trigger": {"skill": "place", "args": {"object": "mug", "support": "storage_bin"}},
         "to": {"support": "dining_table_2/top", "xy": [3.5, 6.0]}, "report": [["inside", "mug", "storage_bin"]]}
    inj, base, rig = make([f], monkeypatch, atoms=lambda a: [{"atom": str(x), "holds": False, "detail": ""} for x in a])
    monkeypatch.setattr(R.FailureRunner, "_pose_on", lambda self, n, to: ([3.5, 6.0, 0.8], [1, 0, 0, 0]))
    for _ in range(2):
        inj.run("pick", {"object": "mug"})
        assert not inj.run("place", {"object": "mug", "support": "storage_bin"}).success
    inj.run("pick", {"object": "mug"})
    assert inj.run("place", {"object": "mug", "support": "dining_table_2/top"}).success   # another place works


def test_slip_past_the_edge_falls_back_onto_the_support(monkeypatch):
    fs = [{"id": "s", "kind": "slip", "trigger": {"skill": "navigate", "while_holding": "mug"}}]
    inj, base, rig = make(fs, monkeypatch)
    p0 = rig.poses["mug"][0].copy()
    inj.run("pick", {"object": "mug"})
    rig.poses["mug"] = (p0 + [0, -0.1, 0.05], rig.poses["mug"][1])          # lifted and drawn over the edge
    seq = iter([None, "kitchen_island/top"])                                  # fell off, then back on the island
    monkeypatch.setattr(R.FailureRunner, "_support_of", lambda self, n: next(seq))
    real_release = R.FailureRunner._release
    def drop(self):
        real_release(self)
        rig.poses["mug"] = (np.array([1.0, 0.9, 0.05]), rig.poses["mug"][1])   # on the floor
        return 0.0
    monkeypatch.setattr(R.FailureRunner, "_release", drop)
    assert "slipped" in inj.run("navigate", {"destination": "a"}).error
    assert np.allclose(rig.poses["mug"][0], p0) and inj.failure_log[-1]["restored"] is True
