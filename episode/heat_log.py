"""Which appliance heated each food (bench side; zeno_skills/thermal.py is untouched).

``track(rig)`` wraps ``rig.thermal.step``: after every step, each food whose temperature rose is credited to the
stove when the stove is on and the food sits on a burner (in a vessel or on it), else to the microwave.  The totals
(degrees C per appliance) land in ``rig.memory["heated_by"]``; the goal predicate ``heated_by`` reads them.
T07 microwave_works (user 11-11): heating on the stove when the microwave works costs a tier.
"""
from __future__ import annotations


def track(rig) -> None:
    th = getattr(rig, "thermal", None)
    if th is None or getattr(th, "_heat_logged", False):
        return
    from zeno_skills.thermal import on_burner_vessel
    log = rig.memory.setdefault("heated_by", {})
    step = th.step
    stoves = {name for name, src in th.sources.items() if src.get("kind") == "stove"}

    def logged_step(rig_, dt):
        before = dict(th.temperatures_c)
        step(rig_, dt)
        apps = {a["name"]: a for a in getattr(rig_.ann, "appliances", [])}
        for food, t in th.temperatures_c.items():
            gain = t - before.get(food, t)
            if gain <= 0:
                continue
            src = next((s for s in stoves if th.on.get(s) and s in apps
                        and on_burner_vessel(rig_, food, apps[s]) is not None), None) or th.appliance
            per = log.setdefault(food, {})
            per[src] = per.get(src, 0.0) + gain

    th.step = logged_step
    th._heat_logged = True
