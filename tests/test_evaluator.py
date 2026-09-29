"""Evaluator on synthetic states (no simulator):  python -m pytest tests/"""

import json
import math
from pathlib import Path

import numpy as np

from zeno_skills.annotations import SceneAnnotations
from zeno_skills.evaluator import TaskEvaluator

ROOT = Path(__file__).resolve().parents[1]


def load(task):
    t = json.loads((ROOT / f"tasks/{task}/task.json").read_text())
    ann = SceneAnnotations(ROOT / t["annotation"])
    return t, ann


def start_state(task, ann):
    """Objects at their annotated (settled) positions, yaw from task.json."""
    objs = {}
    for name, o in ann.objects.items():
        yaw = task["placed_objects"].get(name, {}).get("yaw", 0.0)
        objs[name] = {"pos": list(o["position"]), "quat": [math.cos(yaw / 2), 0, 0, math.sin(yaw / 2)]}
    return {"objects": objs, "joints": {a["name"]: a["closed_q"] for a in ann.articulated}}


def put_inside(ev, st, name, cont, dx=0.0):
    """Move ``name`` so its bottom rests on the container floor."""
    cb = ev.bottom(cont, st)
    a = ev._asset(name)
    q = st["objects"][name]["quat"]
    st["objects"][name] = {"pos": list(cb + np.array([dx, 0, 0.015]) - np.asarray(a["origin_to_bottom_center"])),
                           "quat": q}


def test_collect_fruits_start_fails_goal_passes():
    t, ann = load("collect_fruits")
    st = start_state(t, ann)
    ev = TaskEvaluator(t, ann, initial_state=st)
    rep = ev.evaluate(st)
    assert not rep["success"]
    cont = rep["bindings"]["container"]
    for k, f in enumerate(t["roles"]["fruit"]):
        put_inside(ev, st, f, cont, dx=0.05 * (k - 1))
    rep = ev.evaluate(st)
    assert rep["success"], rep
    assert rep["progress"] == 1.0
    # an open door breaks "closed"
    a = ann.articulated[0]
    st["joints"][a["name"]] = a["open_q"]
    rep = ev.evaluate(st)
    assert not rep["success"] and [r["ok"] for r in rep["conditions"]] == [True, True, False, True]


def test_dropped_object_detected():
    t, ann = load("collect_fruits")
    st = start_state(t, ann)
    ev = TaskEvaluator(t, ann, initial_state=json.loads(json.dumps(st)))
    st["objects"]["orange"]["pos"][2] = 0.03
    rep = ev.evaluate(st)
    row = next(r for r in rep["conditions"] if r["type"] == "not_dropped")
    assert not row["ok"] and "orange" in row["items"][0]["detail"]


def test_breakfast_alternatives():
    t, ann = load("breakfast_setup")
    st = start_state(t, ann)
    ev = TaskEvaluator(t, ann, initial_state=st)
    rep = ev.evaluate(st)
    on_rows = [r for r in rep["conditions"] if r["type"] == "on"]
    # plate and spoon start on the table (only the place setting is missing), the cup does not
    assert [r["ok"] for r in on_rows] == [True, False, True]
    near = next(r for r in rep["conditions"] if r["type"] == "near")
    assert not near["ok"]
    # without the plate, a bowl on the table satisfies the "plate|bowl" slot
    del st["objects"]["plate"]
    ev = TaskEvaluator(t, ann, initial_state=st)
    ev.slots.present.discard("plate")
    bowl = "bowl"
    s = ann.support(t["goal"]["all"][0]["support"])
    a = ev._asset(bowl)
    st["objects"][bowl]["pos"] = [2.95, 6.70, s["z"] + 0.001 - a["origin_to_bottom_center"][2]]
    st["objects"][bowl]["quat"] = [1, 0, 0, 0]
    rep = ev.evaluate(st)
    assert rep["conditions"][0]["ok"] and rep["conditions"][0]["items"][0]["instance"] == bowl


def test_heat_breakfast_requires_measured_temperature():
    from zeno_skills.thermal import ThermalModel
    t, ann = load("heat_breakfast")
    st = start_state(t, ann)
    model = ThermalModel(t["thermal"])
    st["temperatures_c"] = dict(model.temperatures_c)
    ev = TaskEvaluator(t, ann, initial_state=st)
    assert not ev.evaluate(st)["conditions"][0]["ok"]
    model.active = True
    model.advance(15.0, [], True)
    assert model.temperatures_c["oatmeal"] == 4.0
    model.advance(14.0, ["oatmeal"], False)
    assert model.temperatures_c["oatmeal"] == 4.0 and not model.active
    model.active = True
    model.advance(14.0, ["oatmeal"], True)
    st["temperatures_c"] = dict(model.temperatures_c)
    assert ev.evaluate(st)["conditions"][0]["ok"]
