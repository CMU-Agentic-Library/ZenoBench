"""episode.heat_log credits each food's warming to the stove or the microwave (T07 microwave_works scoring)."""
from types import SimpleNamespace

import zeno_skills.thermal as thermal
from episode.goal_predicates import GOAL_PREDICATES
from episode.heat_log import track


class FakeThermal:
    def __init__(self):
        self.sources = {"kitchen_microwave": {"kind": "microwave"}, "kitchen_stove": {"kind": "stove"}}
        self.appliance = "kitchen_microwave"
        self.temperatures_c = {"oatmeal": 4.0}
        self.on = {"kitchen_microwave": False, "kitchen_stove": False}

    def step(self, rig, dt):
        if any(self.on.values()):
            self.temperatures_c["oatmeal"] += 2.0 * dt


def test_heat_log(monkeypatch):
    on_burner = {"v": False}
    monkeypatch.setattr(thermal, "on_burner_vessel", lambda rig, food, app: "bowl" if on_burner["v"] else None)
    rig = SimpleNamespace(thermal=FakeThermal(), memory={},
                          ann=SimpleNamespace(appliances=[{"name": "kitchen_stove"}]))
    track(rig)
    track(rig)                                    # idempotent
    rig.thermal.on["kitchen_microwave"] = True
    rig.thermal.step(rig, 5.0)                    # +10 C in the microwave
    rig.thermal.on.update(kitchen_microwave=False, kitchen_stove=True)
    on_burner["v"] = True
    rig.thermal.step(rig, 1.0)                    # +2 C on the stove
    assert rig.memory["heated_by"]["oatmeal"] == {"kitchen_microwave": 10.0, "kitchen_stove": 2.0}
    pred = GOAL_PREDICATES["heated_by"].evaluate
    assert pred(rig, {}, "oatmeal", "kitchen_stove", 0.5)[0]
    assert not pred(rig, {}, "oatmeal", "kitchen_stove", 5.0)[0]
    assert not pred(SimpleNamespace(memory={}), {}, "oatmeal", "kitchen_stove")[0]
