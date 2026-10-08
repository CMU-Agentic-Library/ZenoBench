"""Task-level food temperature: microwave and stove heating, refrigerator cooling.

This is an explicit state model, not PhysX heat transfer.  Each food item in
``task["thermal"]`` has ``initial_c`` and optional ``heating_rate_c_per_s``
(microwave), ``stove_rate_c_per_s`` and ``cooling_rate_c_per_s``.

Heat sources (``task["thermal_sources"]``, defaults below):

* microwave — heats food inside its cavity while ``active`` and the door is
  closed; opening the door stops the cycle (unchanged from the original model).
* stove     — heats food inside a container whose bottom rests on the burner
  disc while the burner is on.  The burner is switched by the physical power
  button.
* refrigerator — cools food inside the body box toward ``fridge_c`` while its
  door is closed.

``ThermalModel.active`` remains the microwave cycle flag used by existing code.
"""

from __future__ import annotations

import math

DEFAULT_SOURCES = {"kitchen_microwave": {"kind": "microwave"},
                   "breakfast_fridge": {"kind": "refrigerator", "fridge_c": 4.0},
                   "kitchen_stove": {"kind": "stove"}}


class ThermalModel:
    def __init__(self, config, appliance="kitchen_microwave", sources=None):
        self.config = config
        self.appliance = appliance
        self.sources = dict(DEFAULT_SOURCES if sources is None else sources)
        self.temperatures_c = {name: float(v["initial_c"]) for name, v in config.items()}
        self.on = {name: False for name in self.sources}

    # The microwave cycle flag, kept for the original heating code path.
    @property
    def active(self):
        return self.on.get(self.appliance, False)

    @active.setter
    def active(self, value):
        self.on[self.appliance] = bool(value)

    def advance(self, dt, objects_inside, door_closed):
        """Original microwave-only update (kept for callers and tests)."""
        if not door_closed:
            self.active = False
        if not self.active or not door_closed:
            return
        for name in objects_inside:
            if name in self.config:
                self.temperatures_c[name] += float(self.config[name]["heating_rate_c_per_s"]) * dt

    def step(self, rig, dt):
        ann = rig.ann
        arts = {a["name"]: a for a in ann.articulated}
        appliances = {a["name"]: a for a in getattr(ann, "appliances", [])}
        for name, src in self.sources.items():
            kind = src["kind"]
            if kind == "microwave" and name in arts:
                a = arts[name]
                closed = abs(rig.joint(name) - a["closed_q"]) <= 0.10
                b = a["cavity_aabb"]
                inside = []
                if closed and self.on.get(name):
                    for food in self.config:
                        if food in rig._bodies:
                            p, _ = rig.obj_pose(food)
                            if all(b[i] + 0.005 < p[i] < b[i + 3] - 0.005 for i in range(3)):
                                inside.append(food)
                if not closed:
                    self.on[name] = False
                for food in inside:
                    self.temperatures_c[food] += float(self.config[food].get("heating_rate_c_per_s", 0.0)) * dt
            elif kind == "refrigerator" and name in arts:
                a = arts[name]
                if abs(rig.joint(name) - a["closed_q"]) > 0.10:
                    continue
                b = a["body_aabb"]
                target = float(src.get("fridge_c", 4.0))
                for food in self.config:
                    if food not in rig._bodies:
                        continue
                    p, _ = rig.obj_pose(food)
                    if all(b[i] < p[i] < b[i + 3] for i in range(3)):
                        rate = float(self.config[food].get("cooling_rate_c_per_s", 1.0))
                        t = self.temperatures_c[food]
                        self.temperatures_c[food] = max(target, t - rate * dt)
            elif kind == "stove" and name in appliances and self.on.get(name):
                for food in self.config:
                    if food not in rig._bodies:
                        continue
                    vessel = on_burner_vessel(rig, food, appliances[name])
                    if vessel is not None:
                        rate = float(self.config[food].get("stove_rate_c_per_s", 2.0))
                        self.temperatures_c[food] += rate * dt


def burners_of(appliance):
    return appliance.get("burners") or [appliance["burner"]]


def on_burner_vessel(rig, food, appliance):
    """The object resting on a burner disc of the stove that contains ``food``
    (or the food itself when it sits directly on a burner), else None."""
    st = rig.state()

    def on_disc(name):
        b = rig.geo.bottom(name, st)
        return any(math.hypot(b[0] - bu["center"][0], b[1] - bu["center"][1]) <= bu["radius"] + 0.03
                   and abs(b[2] - bu["center"][2]) <= 0.03 for bu in burners_of(appliance))

    if on_disc(food):
        return food
    for vessel, o in rig.ann.objects.items():
        if vessel != food and rig.ann.asset_of(o).get("container") and on_disc(vessel):
            if rig.geo.inside(food, vessel, st)[0]:
                return vessel
    return None
