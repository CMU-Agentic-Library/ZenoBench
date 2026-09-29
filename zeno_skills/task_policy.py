"""Goal-driven scripted policy: task.json + annotations -> skill calls.

Nothing is task-specific.  The policy reads the goal conditions (see
evaluator.py), evaluates them on the simulator state and, for every
unsatisfied one, chooses an object instance and a skill sequence:

  inside  C   pick each missing slot, place "in:<container>"; the container is
              the first present alternative ("toy_box|storage_basket"); a
              container that keeps refusing objects is swapped for the next
  on      S   pick the slot's first workable instance ("plate|bowl": plates
              nearest first, then bowls), place it on a free spot of S near
              the place hint (hints may also list support levels, e.g. the
              shelves of two bookcases in order)
  near        items already on the support but far from their hints are moved
  closed      close every door/drawer that is open
Failed picks mark the instance and fall through to the next alternative;
failed places try other spots, other listed surfaces, then put the object
back.  Every branch taken is recorded in ``decisions``.
"""

from __future__ import annotations

import math
import time

import numpy as np

from . import skills as S
from .rig import Dropped, SkillFailure
from .tasks import place_name


class TaskPolicy:
    def __init__(self, rig, task, evaluator, max_seconds=3600):
        self.rig, self.task, self.ev = rig, task, evaluator
        self.hints = task.get("place_hints", {})
        self.failed = {}            # instance -> reason: never retried
        self.bad_containers = set()
        self.decisions = []
        self.deadline = time.time() + max_seconds

    # ------------------------------------------------------------ bookkeeping
    def decide(self, kind, **kw):
        d = {"t": round(self.rig.tick / 120, 1), "kind": kind, **kw}
        self.decisions.append(d)
        self.rig.log("decision", **d)

    def _hint(self, inst, slot_label):
        for key in [inst, slot_label] + slot_label.split("|") + self._roles_of(inst):
            if key in self.hints:
                return self.hints[key]
        return None

    def _roles_of(self, inst):
        return [r for r, v in self.ev.slots.roles.items() if inst in v]

    def _dist(self, inst):
        x, y, _ = self.rig.base_pose()
        p, _ = self.rig.obj_pose(inst)
        return math.hypot(p[0] - x, p[1] - y)

    def _enclosing(self, inst):
        """Articulated part whose closed carcass holds the object (a spoon in a
        drawer, a bowl behind a door) while that part is closed, or None."""
        p, _ = self.rig.obj_pose(inst)
        for a in self.rig.ann.articulated:
            b = a.get("body_aabb")
            if b and b[0] < p[0] < b[3] and b[1] < p[1] < b[4] and b[2] < p[2] < b[5] - 0.02:
                q = self.rig.joint(a["name"])
                if abs(q - a["open_q"]) > 0.15 * abs(a["open_q"] - a["closed_q"]):
                    return a["name"]
        return None

    def _enclosed(self, inst):
        return self._enclosing(inst) is not None

    def _order(self, cands, label):
        """Alternatives keep their order ("plate|bowl": plates before bowls);
        within one alternative the nearest instance first; instances shut in
        a cabinet last."""
        alts = label.split("|")

        def group(inst):
            for k, alt in enumerate(alts):
                if inst in self.ev.slots.instances(alt):
                    return k
            return len(alts)
        return sorted(dict.fromkeys(cands), key=lambda i: (self._enclosed(i), group(i), self._dist(i)))

    # ------------------------------------------------------------ main loop
    def run(self, max_rounds=3):
        for rnd in range(max_rounds):
            rep = self.ev.evaluate(self.rig.state())
            if rep["success"] or time.time() > self.deadline:
                return rep
            self.decide("round", n=rnd, progress=rep["progress"],
                        open=[r["desc"] for r in rep["conditions"] if not r["ok"]])
            order = sorted(range(len(self.ev.goal["all"])), key=lambda i: self._rank(self.ev.goal["all"][i]))
            progressed = False
            for i in order:
                if time.time() > self.deadline:
                    break
                cond = self.ev.goal["all"][i]
                rep = self.ev.evaluate(self.rig.state())
                row = rep["conditions"][i]
                if row["ok"]:
                    continue
                progressed |= bool(self._fix(cond, row, rep))
            if not progressed:
                break
        return self.ev.evaluate(self.rig.state())

    @staticmethod
    def _rank(c):
        if "on" in c and any(s.startswith("$") for s in c["on"]):
            return 0                # move the container first
        return {"inside": 1, "on": 2, "near": 3, "upright": 4, "closed": 5}.get(
            next((k for k in c if k in ("on", "inside", "near", "upright", "closed", "not_dropped")), ""), 9)

    def _fix(self, c, row, rep):
        if "inside" in c:
            return self._fix_inside(c, row, rep)
        if "on" in c:
            return self._fix_on(c, row, rep)
        if "near" in c:
            return self._fix_near(c, row, rep)
        if "closed" in c:
            return self._fix_closed(c, row)
        return False

    # ------------------------------------------------------------ primitives
    def _pick(self, inst, why, attempts=2):
        """Pick with one retry (a slipped grasp is often fine the second
        time); planning failures are not retried."""
        if inst in self.failed:
            return False
        if self.rig.held is not None:
            self._put_back_held()
        self.rig.caption = f"TASK: {why}"
        reason = ""
        for k in range(attempts):
            try:
                S.pick(self.rig, inst)
                return True
            except SkillFailure as e:
                reason = str(e)
                self.decide("pick_failed", instance=inst, attempt=k + 1, reason=reason)
                if self.rig.held is not None or reason.split(": ", 1)[-1].startswith("no "):
                    break               # planning failure ("no reachable grasp..."): retrying won't help
        self.failed[inst] = reason
        return False

    def _carry(self, inst, why, place, max_drops=2):
        """Pick inst and run place(); an object that slips out of the hand on
        the way is picked up again where it fell."""
        for k in range(max_drops + 1):
            if not self._pick(inst, why):
                return False
            try:
                return place()
            except Dropped as e:
                self.decide("dropped", instance=inst, n=k + 1, reason=str(e))
        self.failed[inst] = "keeps slipping out of the hand"
        return False

    def _open_to_reach(self, inst):
        """Object shut in a cabinet/drawer: open it first (the final 'closed'
        condition shuts it again)."""
        art = self._enclosing(inst)
        if art is None:
            return True
        if self.rig.held is not None:
            self._put_back_held()
        self.decide("open_to_reach", instance=inst, part=art)
        try:
            self.rig.caption = f"TASK: open the {self.rig.ann.art(art)['category']} to reach {inst}"
            S.open_articulated(self.rig, art)
        except SkillFailure as e:
            self.failed[inst] = f"could not open {art}: {e}"
            self.decide("open_failed", instance=inst, part=art, reason=str(e))
            return False
        if self._enclosed(inst):
            self.failed[inst] = f"still inside {art} after opening it"
            self.decide("still_enclosed", instance=inst, part=art)
            return False
        return True

    def _put_back_held(self):
        """Holding something we could not place: back where it came from,
        else set it down on any surface in reach, else drop it."""
        h = self.rig.held
        name = h["name"]
        src = self.rig.ann.objects[name].get("support")
        try:
            if src:
                S.place_on(self.rig, name, src)
                self.decide("put_back", instance=name, support=src)
                return
        except SkillFailure as e:
            self.decide("put_back_failed", instance=name, reason=str(e))
        if self.rig.held is not None:
            self.rig.grip(h["pre_open"], 60)
            self.rig.held = None
            self.decide("released", instance=name)

    def _surfaces(self, place, inst, slot_label):
        """Surfaces to try for an 'on' goal: the hint's list if it names
        surfaces, else every surface of the goal place with room for the object."""
        hint = self._hint(inst, slot_label)
        places = place if isinstance(place, list) else [place]
        names = []
        for p in places:
            if isinstance(p, dict):
                continue
            for s in self.ev.surfaces(p):
                names.append(s["name"])
        if isinstance(hint, list) and hint and isinstance(hint[0], str):
            ordered = [h for h in hint if h in names] + [n for n in names if n not in hint]
            xy = None
        else:
            h_obj = self.rig.ann.asset_of(self.rig.ann.objects[inst])["size"][2]
            ordered = sorted(names, key=lambda n: -self.rig.ann.support(n)["z"])
            ordered = [n for n in ordered if self.rig.ann.support(n).get("clearance", 1.0) > h_obj + 0.08]
            xy = hint
        return ordered, xy

    def _place_on(self, inst, place, slot_label):
        names, xy = self._surfaces(place, inst, slot_label)
        last = None
        for sname in names:
            try:
                self.rig.caption = f"TASK: put {inst} on {sname.split('_spawn')[0]}"
                S.place_on(self.rig, inst, sname, xy)
                return True
            except Dropped:
                raise
            except SkillFailure as e:
                last = str(e)
                self.decide("surface_failed", instance=inst, surface=sname, reason=last)
                if self.rig.held is None:
                    return False
        self.decide("place_failed", instance=inst, reason=last)
        self._put_back_held()
        return False

    # ------------------------------------------------------------ conditions
    def _fix_on(self, c, row, rep):
        done = False
        slots = self.ev.slots.expand(c["on"], rep["bindings"])
        where = "shelf" if isinstance(c["support"], list) else place_name(c["support"])
        for (label, cands), item in zip(slots, row["items"]):
            if item["ok"]:
                continue
            ok = False
            ordered = self._order(cands, label)
            for k, inst in enumerate(ordered):
                if inst in self.failed:
                    continue
                if k:
                    self.decide("alternative", slot=label, instance=inst,
                                because={i: self.failed.get(i, "enclosed") for i in ordered[:k]})
                if not self._open_to_reach(inst):
                    continue
                if self._carry(inst, f"{label} -> {where}", lambda: self._place_on(inst, c["support"], label)):
                    ok = done = True
                    break
                self.failed.setdefault(inst, "could not be placed")
            if not ok:
                self.decide("slot_unsatisfied", slot=label)
        return done

    def _container(self, c, row, rep):
        """Keep the container that already holds something; otherwise the
        first present alternative that has not refused objects."""
        cands = [i for i in self.ev.slots.expand([c["container"]], rep["bindings"])[0][1]
                 if i not in self.bad_containers]
        if row.get("container") in cands and row["n_ok"] > 0:
            return row["container"]
        return cands[0] if cands else None

    def _fix_inside(self, c, row, rep):
        cont = self._container(c, row, rep)
        if cont is None:
            self.decide("no_container", slots=c["inside"])
            return False
        if cont != c["container"].split("|")[0]:
            self.decide("alternative", slot=c["container"], instance=cont,
                        skipped=[i for i in c["container"].split("|") if i != cont])
        done, refused = False, 0
        for label, cands in self.ev.slots.expand(c["inside"], rep["bindings"]):
            st = self.rig.state()
            if any(self.ev.inside(i, cont, st)[0] for i in cands):
                continue
            for inst in self._order(cands, label):
                if not self._open_to_reach(inst):
                    continue
                try:
                    if self._carry(inst, f"{label} -> {cont}", lambda: S.place(self.rig, inst, "in:" + cont)):
                        done = True
                        break
                    continue
                except SkillFailure as e:
                    refused += 1
                    self.decide("container_refused", container=cont, instance=inst, reason=str(e))
                    if self.rig.held is not None:
                        self._put_back_held()
                    if refused >= 2:
                        self.bad_containers.add(cont)
                        self.decide("container_swapped", container=cont)
                        return done
        return done

    def _fix_near(self, c, row, rep):
        done = False
        st = self.rig.state()
        for label, cands in self.ev.slots.expand(c["near"], rep["bindings"]):
            on_sup = [i for i in cands if self.ev.on(i, c["support"], st)[0]]
            if not on_sup:
                continue
            hint = self._hint(on_sup[0], label)
            if hint is None or isinstance(hint[0], str):
                continue
            best = min(on_sup, key=lambda i: np.linalg.norm(self.ev.bottom(i, st)[:2] - np.asarray(hint)))
            if np.linalg.norm(self.ev.bottom(best, st)[:2] - np.asarray(hint)) < 0.15:
                continue
            self.decide("regroup", slot=label, instance=best, hint=hint)
            if self._carry(best, f"bring {label} to the place setting",
                           lambda: self._place_on(best, c["support"], label)):
                done = True
        return done

    def _fix_closed(self, c, row):
        done = False
        st = self.rig.state()
        arts = self.rig.ann.articulated if c["closed"] == "all" else [self.rig.ann.art(n) for n in c["closed"]]
        for a in arts:
            q = st["joints"][a["name"]]
            if abs(q - a["closed_q"]) <= (0.10 if a["type"] == "revolute" else 0.04):
                continue
            if self.rig.held is not None:
                self._put_back_held()
            try:
                self.rig.caption = f"TASK: close the {a['category']}"
                S.close_articulated(self.rig, a["name"])
                done = True
            except SkillFailure as e:
                self.decide("close_failed", part=a["name"], reason=str(e))
        return done
