"""Failure injection at run time: a proxy in front of an Episode's Contract runner.

    from failure_injection.runtime import install
    inj = install(ep, cfg)          # cfg = benchmark.scene.episode_config(...); no-op without "failures"
    ...
    inj.failure_log                 # for the evaluation only

The proxy changes nothing but the declared calls.  Every effect is applied to the simulator and
then left to physics (an opened hand drops the object, a teleported object settles, a closed door
stays closed); the planner learns about it only through the call's ordinary feedback (an error code
and measured pre/postconditions, worded like the natural failures) and through what it observes
next.  The failure specs, the trigger counts and ``failure_log`` never reach the planner.
"""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import numpy as np

from failure_injection.spec import ACTION_KINDS, BASE_SKILLS, mode, seeded, validate

ROOT = Path(__file__).resolve().parents[1]
RELEASE_W = 0.04


class FailureRunner:
    def __init__(self, base, rig, failures, cfg, episode=None):
        self._base, self.rig, self.cfg, self.episode = base, rig, cfg, episode
        self.failures = [dict(f, _seeded=seeded(f, cfg["task_id"], cfg["variant"], cfg["seed"])) for f in failures]
        self.counts: Counter = Counter()
        self.fired: dict[str, dict] = {}
        self.failure_log: list[dict] = []
        self.ik_block: dict | None = None
        self.call_index = 0
        self._assets = json.loads((ROOT / "annotations/assets.json").read_text())
        self._supports = {s["name"]: s for s in rig.ann.supports}

    def __getattr__(self, name):
        return getattr(self._base, name)

    def contract(self, key):
        return self._base.contract(key)

    # ------------------------------------------------------------------ trigger matching
    def _matches(self, f, verb, args):
        t = f.get("trigger") or {}
        if t.get("skill") != verb:
            return False
        if any(args.get(k) != v for k, v in (t.get("args") or {}).items()):
            return False
        if t.get("while_holding") and (self.rig.held or {}).get("name") != t["while_holding"]:
            return False
        if f.get("after_fired") and f["after_fired"] not in self.fired:
            return False
        return f["id"] not in self.fired

    def _due(self, f, verb, args):
        """Count a matching call; True when this is the nth."""
        if not self._matches(f, verb, args):
            return False
        self.counts[f["id"]] += 1
        return self.counts[f["id"]] == int(f["trigger"].get("nth", 1))

    def _record(self, f, manifested, **detail):
        row = {"id": f["id"], "kind": f["kind"], "mode": mode(f), "call_index": self.call_index,
               "tick": int(getattr(self.rig, "tick", 0)), "manifested": bool(manifested), **detail}
        self.fired[f["id"]] = row
        self.failure_log.append(row)
        self.rig.log("failure_event", **{k: v for k, v in row.items() if k != "id"}, fid=f["id"])
        return row

    # ------------------------------------------------------------------ run
    def run(self, key, args, depth=0):
        c = self._base.contract(key)
        verb = c["verb"]
        args = dict(args)
        self.call_index += 1
        # IK: refused before any motion, until the base is re-parked by a base skill
        blk = self.ik_block
        if blk and verb == blk["verb"] and _target(args) == blk["target"]:
            blk["refusals"] += 1
            return self._refuse(c, args, "POLICY_FAILED", blk["message"])
        for f in self.failures:
            if f["kind"] == "ik" and self._due(f, verb, args):
                msg = f"{_stage(verb)}: no IK solution reaches {_target(args)} from this base pose"
                self.ik_block = {"verb": verb, "target": _target(args), "message": msg, "refusals": 1,
                                 "until": f.get("until", "base_skill"), "fid": f["id"]}
                self._record(f, True, verb=verb, target=_target(args), base=list(map(float, self.rig.base_pose())))
                if self.ik_block["until"] == "once":
                    self.ik_block = None
                return self._refuse(c, args, "POLICY_FAILED", msg)
            if f["kind"] == "slip" and self._due(f, verb, args):
                name = f["trigger"]["while_holding"]
                self._release()
                self._record(f, True, object=name, landed_on=self._support_of(name))
                return self._refuse(c, args, "POLICY_FAILED", f"carry: {name} slipped out of the hand while carrying it")
        res = self._base.run(key, args, depth)
        if self.ik_block and verb in BASE_SKILLS and res.success:
            self.ik_block = None                          # re-parked: the next attempt plans from a new pose
        for f in self.failures:
            if f["kind"] == "grasp" and self._due(f, verb, args):
                if not res.success:
                    self._record(f, False, note="the pick already failed on its own")
                    continue
                name = args.get("object")
                lift = self._release()
                self._record(f, True, object=name, landed_on=self._support_of(name))
                _fail(res, "POLICY_FAILED", f"pick_lift: {name} not held (lift {lift:.3f} m)",
                      lambda a: a.startswith("holding("))
            elif f["kind"] == "placement" and self._due(f, verb, args):
                if not res.success:
                    self._record(f, False, note="the place already failed on its own")
                    continue
                self._placement(f, args.get("object"), res)
        for f in self.failures:
            if mode(f) == "dynamic" and (res.success or f["trigger"].get("on") == "any") and self._due(f, verb, args):
                self._event(f)
        return res

    # ------------------------------------------------------------------ effects
    def _refuse(self, c, args, code, msg):
        from zeno_skills.skill_runtime import SkillResult
        action = f"{c['action_predicate']['name']}(" + ", ".join(
            f"{k}={args[k]}" for k in c["action_predicate"]["arguments"] if args.get(k) is not None) + ")"
        res = SkillResult(c["contract_id"], c["skill_id"], action, False, None, [], [], [], {}, {},
                          error=msg, error_code=code)
        self.rig.log("contract_end", contract=c["contract_id"], action=action, success=False, path=None, error=msg)
        self._base.trace.append(res.asdict())
        return res

    def _release(self) -> float:
        """Open the right hand over where it is; the object falls under physics."""
        rig = self.rig
        name = (rig.held or {}).get("name")
        z0 = float(rig.obj_pose(name)[0][2]) if name else 0.0
        rig.grip(RELEASE_W, 60)
        rig.held = None
        rig.step(120)
        return max(0.0, float(rig.obj_pose(name)[0][2]) - z0) if name else 0.0

    def _support_of(self, name):
        st = self.rig.state()
        s = self.rig.geo.support_under(name, st) if name in st["objects"] else None
        return s["name"] if s else None

    def _teleport(self, name, pos, quat_wxyz, settle=120):
        rig = self.rig
        t = rig.torch
        b = rig._bodies[name]
        b.set_world_pose(t.tensor(np.asarray(pos, float), dtype=t.float32),
                         t.tensor(np.asarray(quat_wxyz, float), dtype=t.float32))
        b.set_linear_velocity(t.zeros(3))
        b.set_angular_velocity(t.zeros(3))
        rig.step(settle)

    def _pose_on(self, name, to):
        from benchmark.scene import overlay_pose
        asset = self.rig.ann.asset_of(self.rig.ann.objects[name])
        return overlay_pose(asset, to, self._supports)

    def _placement(self, f, name, res):
        rig = self.rig
        if f["mode"] == "tipped":
            p, q = rig.obj_pose(name)
            asset = rig.ann.asset_of(rig.ann.objects[name])
            yaw = 2 * math.atan2(q[3], q[0])
            # on its side: a quarter turn about the object's own x axis, then dropped from 1 cm above its half size
            qx = [math.cos(math.pi / 4), math.sin(math.pi / 4), 0.0, 0.0]
            qz = [math.cos(yaw / 2), 0.0, 0.0, math.sin(yaw / 2)]
            c = rig.geo.centre(name, rig.state())
            bottom = rig.geo.bottom(name, rig.state())
            pos = np.array([c[0], c[1], bottom[2] + max(asset["size"][0], asset["size"][1]) / 2 + 0.01])
            # keep the box centre where it was in xy; origin offset rotated with the new orientation
            R = _quat_R(_qmul(qz, qx))
            off = np.asarray(asset["origin_to_bottom_center"], float) + np.array([0, 0, asset["size"][2] / 2])
            self._teleport(name, pos - R @ off, _qmul(qz, qx))
            detail = {"mode": "tipped"}
        else:
            to = dict(f["to"])
            d = f["_seeded"].get("dxy")
            if d:
                to["xy"] = [to["xy"][0] + d[0], to["xy"][1] + d[1]]
            pos, q = self._pose_on(name, to)
            self._teleport(name, pos, q)
            detail = {"mode": "displaced", "to": to}
        rows = self._atoms(f["report"])
        bad = [r for r in rows if not r["holds"]]
        self._record(f, bool(bad), object=name, **detail, report=rows)
        if bad:
            _fail(res, "POSTCONDITION_FAILED", "; ".join(f"{r['atom']} is false ({r['detail']})" for r in bad))
            res.postconditions = list(res.postconditions) + [{"atom": r["atom"], "holds": r["holds"],
                                                              "detail": r["detail"]} for r in rows]

    def _event(self, f):
        rig = self.rig
        ev = f["event"]
        if ev["type"] in ("move_object", "into"):
            name = ev["object"]
            if name in {(rig.held or {}).get("name"), (getattr(rig, "left_held", None) or {}).get("name")}:
                self._record(f, False, note=f"{name} is in the robot's hand; not moved")
                return
            if ev["type"] == "move_object":
                to = dict(ev["to"])
                d = f["_seeded"].get("dxy")
                if d:
                    to["xy"] = [to["xy"][0] + d[0], to["xy"][1] + d[1]]
            else:
                st = rig.state()
                cont = ev["container"]
                cc, cb = rig.geo.centre(cont, st), rig.geo.bottom(cont, st)
                off = ev.get("offset_xy", [0.0, 0.0])
                to = {"xy": [float(cc[0]) + off[0], float(cc[1]) + off[1]],
                      "z": float(cb[2]) + float(ev.get("floor_m", 0.012)), "yaw_deg": ev.get("yaw_deg", 0.0)}
            pos, q = self._pose_on(name, to)
            self._teleport(name, pos, q)
            self._record(f, True, event=ev["type"], object=name, to=to, landed_on=self._support_of(name))
        elif ev["type"] == "set_joint":
            a = next(x for x in rig.ann.articulated if x["name"] == ev["articulated"])
            v = a["closed_q"] if ev["value"] == "closed" else a["open_q"] if ev["value"] == "open" else float(ev["value"])
            art, dof = rig._arts[a["name"]], rig._dof[a["name"]]
            art.set_joint_positions(np.array([v], dtype=np.float32), joint_indices=np.array([dof]))
            art.set_joint_velocities(np.array([0.0], dtype=np.float32), joint_indices=np.array([dof]))
            rig.step(90)
            self._record(f, True, event="set_joint", articulated=a["name"], value=v, measured=round(rig.joint(a["name"]), 3))

    def _atoms(self, atoms):
        from episode.episode import evaluate_goal
        start = self.episode.start if self.episode is not None else {"objects": {}, "_removed": []}
        return evaluate_goal(self.rig, {"all": atoms}, start)[1]["all"]

    # ------------------------------------------------------------------ start / end
    def check_initial(self):
        for f in self.failures:
            if mode(f) == "initial":
                rows = self._atoms(f["check"])
                self._record(f, all(r["holds"] for r in rows), check=rows)

    def summary(self) -> dict:
        declared = [f["id"] for f in self.failures]
        return {"declared": declared, "fired": sorted(self.fired),
                "manifested": sorted(k for k, v in self.fired.items() if v["manifested"]),
                "not_fired": [i for i in declared if i not in self.fired], "log": self.failure_log}


def _fail(res, code, msg, row_filter=None):
    res.success, res.error_code, res.error = False, code, msg
    res.outputs = {}
    if row_filter is not None:
        for r in res.postconditions:
            if row_filter(r["atom"]):
                r["holds"], r["detail"] = False, "not held"


def _target(args):
    for k in ("object", "articulated", "surface", "button", "container", "lid", "appliance", "target"):
        if args.get(k):
            return args[k]
    return None


def _stage(verb):
    return {"pick": "pick_pre", "place": "place_pre", "drop": "drop_pre", "open": "open_handle",
            "close": "close_handle"}.get(verb, f"{verb}_pre")


def _qmul(a, b):
    w1, x1, y1, z1 = a
    w2, x2, y2, z2 = b
    return [w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2, w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2]


def _quat_R(q):
    w, x, y, z = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def install(episode, cfg):
    """Wrap ``episode.runner`` when the configuration declares failures; returns the proxy or None.
    Must wrap the Contract runner before skill_ext.dispatch.install, so that nested calls of user
    skills meet the same failures."""
    failures = cfg.get("failures")
    if not failures:
        return None
    validate(failures, f"{cfg['task_id']}/{cfg['variant']}", objects=set(episode.rig.ann.objects),
             articulated={a["name"] for a in episode.rig.ann.articulated},
             supports={s["name"] for s in episode.rig.ann.supports})
    inj = FailureRunner(episode.runner, episode.rig, failures, cfg, episode)
    episode.runner = inj
    inj.check_initial()
    return inj
