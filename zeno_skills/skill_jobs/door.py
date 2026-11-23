"""Opening and closing a door or a drawer (motion_skills.Job): the park search's problem -- every way to
hold the handle, every way to push the door, with every empty hand that may do it, one goal -- the
plan to run (skill_plans.plan_door, plan_push), the result."""

from __future__ import annotations

import math
import os

import numpy as np

from ..motion_state import clearing
from ..park_search import VARIANT_COST, Problem
from ..rig import SkillFailure
from ..skill_plans import DOOR_RELAY
from ..tolerances import (DOOR_CLOSED_TOL, DOOR_OPEN_TOL, DRAWER_OPEN_FRAC, HAND_OPENED_FRAC, HANDLE_FINGER_MIN,
                          HANDLE_GAP, PUSH_ABOVE, PUSH_PRE, PUSH_TIP_GAP, PUSH_TRACK, RIDE_DONE_PRIS, RIDE_DONE_REV,
                          RIDE_OVERSHOOT)

DOOR_REACH_IN = 0.12     # m: the reach-in onto the handle starts this far back (the old path's pre-grasp, not measured)
RIDE_STEP_HINGE = 0.10   # rad between the ride's checked samples (skills._ride_check took 8 over the range; not measured)
RIDE_STEP_SLIDE = 0.03   # m ...on a slide
SIDE_TRACK = (0.03, 0.25)    # (lead, rate) of a side hook: the bar loaded through a finger (skills._ride's)
FRONT_TRACK = (0.01, 0.12)   # ...of a front pinch, held by friction only: gently
# PUSH_TRACK, PUSH_ABOVE, PUSH_PRE, PUSH_TIP_GAP: tolerances.py
PUSH_HEIGHTS = (PUSH_ABOVE, -PUSH_ABOVE)   # the push points: above the handle, or below it (two ways of the goal set)


def door_hand(rig, verb, name, args):
    """The hand that opens (closes by the handle): ``args["side"]``, else ZENO_OPEN_SIDE (a diagnostic switch,
    docs 9.3 step 6a), else the empty one -- the right where both are (docs 9.3 step 6b).  SkillFailure
    when it is not empty or a handle is held already."""
    if getattr(rig, "_handle_grasp", None) is not None:
        raise SkillFailure(f"{verb} {name}: a hand holds a handle already")
    empty = [sd for sd in ("right", "left") if (rig.held if sd == "right" else rig.left_held) is None]
    side = args.get("side") or os.environ.get("ZENO_OPEN_SIDE") or (empty[0] if empty else "right")
    if side not in empty:
        raise SkillFailure(f"{verb} {name}: the {side} hand is not empty")
    return side


def handle_closed_on(f, t):
    """The hand closed on a bar ``t`` thick, fingers ``f``: both fingers stopped by it (thin arched
    pulls: ~5 mm).  open_job's after_close and the old open path (skills) alike."""
    lo, frac = HANDLE_FINGER_MIN
    sq_frac, sq_m, slack = HANDLE_GAP
    return bool(f.min() > min(lo, frac * t) and max(sq_frac * t, t - sq_m) < f.sum() < t + slack)


def _ways(a):
    """The ways to hold ``a``'s handle, in order (skills._move_articulated's): (grasp, flip, tilt) --
    the side hook untilted first, tilted 10 / 20 deg for a bar close to its panel, from the far end too
    where the handle allows; a front pinch across an imported bar."""
    h = a["handle"]
    ways = [("side", flip, tilt) for tilt in (0.0, math.radians(10), math.radians(20))
            for flip in ((False, True) if a["type"] == "prismatic" or h.get("flip_ok") else (False,))]
    if h.get("grasp") == "front":            # a round pull: no gap behind it to hook into
        ways = []
    if h.get("pre_open") is not None:        # imported handles (bar geometry annotated)
        ways.append(("front", False, 0.0))
    return ways


def _width(a, grasp):
    """(pre_open, bar thickness) of a grasp on ``a``'s handle (skills._move_articulated's)."""
    h = a["handle"]
    pre_open, t = float(h.get("pre_open", 0.04)), float(h.get("thickness", 0.025))
    if grasp == "front":                     # the fingers straddle the bar across its width
        t = float(np.abs(np.asarray(h["bar_size"], float)) @ np.abs(np.asarray(h["along"], float)))
        pre_open = min(0.04, t / 2 + 0.015)
    return pre_open, t


def door_grips(rig, a, goal):
    """plan_door's grip per way to hold ``a``'s handle (_ways), the part where it stands now: the grasp
    in the part frame (annotations handle_pose at the joint value now), the reach-in along the
    approach, DOOR_REACH_IN long; the ride to ``goal`` (RIDE_OVERSHOOT past it, done RIDE_DONE_REV / RIDE_DONE_PRIS short).
    [(grip, (grasp, flip, tilt), thickness)]."""
    ann = rig.ann
    q0 = rig.joint(a["name"])
    pose = lambda v, a=a: ann.part_pose(a, v)
    sign = 1.0 if goal >= q0 else -1.0
    revolute = a["type"] == "revolute"
    out = []
    for grasp, flip, tilt in _ways(a):
        p, R, appr = ann.handle_pose(a, q0, grasp, flip, tilt)
        pre_open, t = _width(a, grasp)
        lead, rate = FRONT_TRACK if grasp == "front" else SIDE_TRACK
        T = np.eye(4)
        T[:3, :3], T[:3, 3] = R, p
        grip = {"part": a["name"], "kind": "hinge" if revolute else "slider", "pose": pose,
                "T_part_tcp": np.linalg.inv(pose(q0)) @ T, "u": R.T @ np.asarray(appr, float), "L": DOOR_REACH_IN,
                "pre_open": pre_open, "s1": goal + sign * RIDE_OVERSHOOT,
                "ride_step": RIDE_STEP_HINGE if revolute else RIDE_STEP_SLIDE,
                "track": {"lead": lead, "rate": rate, "done": goal - sign * (RIDE_DONE_REV if revolute else RIDE_DONE_PRIS)}}
        out.append((grip, (grasp, flip, tilt), t))
    return out


def open_job(rig, args, state, skill=None):
    """motion_skills.Job of opening ``args["name"]`` to ``args["goal"]`` by its handle: every way to hold
    the handle one goal of the park search (the whole open planned there, skill_plans.plan_door, the
    base riding the part); the plan run with its hooks -- the grip judged and the handle registered as
    held (Rig.snapshot reads it as Held kind "part"), let go -- then judged on the measured joint."""
    from ..motion_skills import Job
    from ..skill_plans import plan_door
    from .base import RigBase
    name = args["name"]
    a = rig.ann.art(name)
    if a.get("handle") is None:
        raise SkillFailure(f"open {name}: no graspable handle annotated")
    side = door_hand(rig, "open", name, args)
    goal = float(a["open_q"] if args.get("goal") is None else args["goal"])
    q0 = rig.joint(name)
    kin, base = rig.arm_kin(side), RigBase(rig)
    build_with = skill.build if skill is not None else plan_door
    grips = door_grips(rig, a, goal)
    if not grips:
        raise SkillFailure(f"open {name}: no way to hold its handle")
    rests = (kin.rest, kin.drive)
    goals = []
    for i, (g, _, _) in enumerate(grips):
        T = np.asarray(g["pose"](q0), float) @ g["T_part_tcp"]
        p, R = T[:3, 3], T[:3, :3]
        pre = p - g["L"] * (R @ g["u"])
        goals.append(((pre, p), (pre, R), VARIANT_COST * i))

    def build(s, k, prior):
        return build_with(kin, s, grips[k][0], rests, base=base, prior=prior, step=0.004)

    problem = Problem(tuple(goals), build, DOOR_RELAY, near=rig.base_pose(), label=f"open {name}", hand=side)
    ctx = {}

    def no_park(diag):
        rig.log("open_no_park", name=name, q=round(q0, 4), goal=round(goal, 4), ways=len(grips), diag=diag)
        return SkillFailure(f"open {name}: no base pose can grasp the handle and ride the motion")

    def found_park(found):
        grasp, flip, tilt = grips[found.k][1]
        rig.log("open_park", park=[round(found.x, 3), round(found.y, 3), round(found.yaw, 1)], side=side,
                hook_side="far" if flip else "near", tilt_deg=round(math.degrees(tilt)), grasp=grasp)
        rig.caption = f"OPEN {a['category']}: go to handle"

    def ready(found):
        grip, (grasp, _, _), t = grips[found.k]
        ctx.update(grip=grip, q0=rig.joint(name))

        def rebuild(st, frm, prior):
            return build_with(kin, st, grip, rests, base=base, start=frm, prior=prior, step=0.004)

        def before_grasp(rig):
            rig.caption = f"OPEN {a['category']}: grasp handle ({'side hook' if grasp == 'side' else 'front pinch'})"

        def after_close(rig):
            f = np.asarray(rig.fingers_of(side), float)[:2]
            if not handle_closed_on(f, t):
                raise clearing(SkillFailure(f"open {name}: handle not grasped, fingers {f.round(4).tolist()}"),
                               grip["pre_open"])
            rig._handle_grasp = {"name": name, "pre_open": grip["pre_open"], "q": rig.joint(name),
                                 "coll_kw": kin.coll_kw, "side": side}
            rig.log("handle_grasped", name=name, fingers=f.round(4).tolist())
            rig.caption = f"OPEN {a['category']}: base follows the joint motion"

        def before_release(rig):
            rig.caption = f"OPEN {a['category']}: release"

        def after_release(rig):
            rig._handle_grasp = None

        hooks = {"door_grasp": {"before": before_grasp}, "door_close_hand": {"after": after_close},
                 "door_release": {"before": before_release, "after": after_release}}
        return found.plan, rebuild, hooks

    def failed(exc):
        # the failure exit (plan_clear) opened the hand: the handle is no longer held
        if getattr(rig, "_handle_grasp", None) is not None and \
                float(np.min(rig.fingers_of(side)[:2])) > HAND_OPENED_FRAC * ctx["grip"]["pre_open"]:
            rig._handle_grasp = None
        return None

    def done():
        q = rig.joint(name)
        rig.log("open_result", name=name, before=ctx["q0"], after=q, goal=goal)
        if a["type"] == "revolute":
            tol = DOOR_OPEN_TOL
        else:                    # a released drawer slides back a little
            tol = DRAWER_OPEN_FRAC * abs(a["open_q"] - a["closed_q"])
        if abs(q - goal) >= tol:
            raise SkillFailure(f"open {name}: joint {ctx['q0']:.3f} -> {q:.3f}, goal {goal:.3f}")
        return q
    return Job(problem=problem, no_park=no_park, found=found_park, ready=ready, failed=failed, done=done)


def push_target(rig, a, q, above=PUSH_ABOVE):
    """(T_part_tcp, n_part) of pushing ``a``'s door at joint value q: the closed fingertips just off the
    panel's outer face (the handle side), ``above`` the handle (clear of the bar), pointing into
    the panel and spread along the hinge axis -- in the part frame, with that face's outward normal
    (skills' old _push_targets, written in the part frame: docs 6, close)."""
    from ..kinematics import gripper_rot
    T = rig.ann.part_pose(a, q)
    Ti = np.linalg.inv(rig.ann.part_pose(a, a["closed_q"]))
    hc = (Ti @ np.r_[np.asarray(a["handle"]["center"], float), 1.0])[:3]      # part frame
    boxes = a.get("part_boxes") or [a["part_box"]]
    lo, hi = (np.asarray(v, float) for v in boxes[0])                      # the panel
    thin = int(np.argmin(hi - lo))
    face = 1.0 if hc[thin] > (lo[thin] + hi[thin]) / 2 else -1.0
    axis = np.asarray(a["axis"], float)
    up = int(np.argmax(np.abs(np.linalg.inv(np.asarray(a["part_frame"], float))[:3, :3] @ axis)))
    c = hc.copy()
    c[thin] = hi[thin] if face > 0 else lo[thin]
    c[up] = float(np.clip(hc[up] + above, lo[up] + 0.04, hi[up] - 0.04))
    width = 3 - thin - up
    c[width] = float(np.clip(hc[width], lo[width] + 0.02, hi[width] - 0.02))
    n = np.zeros(3)
    n[thin] = face
    normal = T[:3, :3] @ n
    contact = (T @ np.r_[c, 1.0])[:3] + normal * PUSH_TIP_GAP
    W = np.eye(4)
    W[:3, :3], W[:3, 3] = gripper_rot(-normal, axis), contact
    return np.linalg.inv(T) @ W, n


def close_job(rig, args, state, skill=None):
    """motion_skills.Job of closing ``args["name"]`` (docs/motion/MOTION_ARCHITECTURE.md 6, close; 9.3 step 6b):
    one park search over every empty hand x every way -- a hinged door pushed shut on its outer face
    (skill_plans.plan_push), the handle held and ridden shut (plan_door, the right hand only) -- the
    push before the handle, the right hand before the left (VARIANT_COST per rank: a weak preference,
    the ranking's manipulability decides most).  The hand that holds something stays where it is
    (the body kept: motion_state.body_locked).  Judged on the measured joint."""
    from ..motion_skills import Job
    from ..skill_plans import DOOR_RELAY, plan_door, plan_push
    from ..skill_plans.door import TORSO
    from .base import RigBase
    name = args["name"]
    a = rig.ann.art(name)
    if a.get("handle") is None:
        raise SkillFailure(f"close {name}: no handle annotated (no push point, no grip)")
    if getattr(rig, "_handle_grasp", None) is not None:
        raise SkillFailure(f"close {name}: a hand holds a handle already")
    empty = [sd for sd in ("right", "left") if (rig.held if sd == "right" else rig.left_held) is None]
    if args.get("side"):
        empty = [sd for sd in empty if sd == args["side"]]
    if not empty:
        raise SkillFailure(f"close {name}: no empty hand")
    goal = float(a["closed_q"])
    q0 = rig.joint(name)
    base = RigBase(rig)
    pose = lambda v, a=a: rig.ann.part_pose(a, v)
    revolute = a["type"] == "revolute"
    sign = 1.0 if goal >= q0 else -1.0
    ways = []                                        # (kind, side, plan input, label)
    if revolute:
        for above in PUSH_HEIGHTS:
            T_tcp, n_part = push_target(rig, a, q0, above)
            push = {"part": name, "pose": pose, "T_part_tcp": T_tcp, "n_part": n_part, "pre": PUSH_PRE, "s1": goal,
                    "ride_step": RIDE_STEP_HINGE, "above": above,
                    "track": {"lead": PUSH_TRACK[0], "rate": PUSH_TRACK[1], "done": goal - sign * RIDE_DONE_REV}}
            ways += [("push", sd, push, None) for sd in empty]
    if "right" in empty:
        for grip, way, t in door_grips(rig, a, goal):
            grip = {**grip, "s1": goal}              # the joint stops at closed: the ride's script ends there
            ways.append(("handle", "right", grip, (way, t)))
    goals = []
    for i, (kind, sd, inp, _) in enumerate(ways):
        F = np.asarray(inp["pose"](q0), float)
        T = F @ np.asarray(inp["T_part_tcp"], float)
        p, R = T[:3, 3], T[:3, :3]
        # the relay: the stand-off off the panel (a push), the reach-in's start (a handle)
        pre = p + inp["pre"] * (F[:3, :3] @ inp["n_part"]) if kind == "push" else p - inp["L"] * (R @ inp["u"])
        goals.append(((pre, p), (pre, R), VARIANT_COST * i, sd))
    kins = {"right": rig.kin, "left": rig.left_kin}

    def build_at(s, k, prior, start=None):
        kind, sd, inp, _ = ways[k]
        kin = kins[sd]
        rests = (kin.rest, kin.drive)
        if kind == "push":
            return plan_push(kin, s, inp, rests, base=base, prior=prior, step=0.004,
                             **({"start": start} if start else {}))
        return plan_door(kin, s, inp, rests, base=base, prior=prior, step=0.004, **({"start": start} if start else {}))

    problem = Problem(tuple(goals), lambda s, k, prior: build_at(s, k, prior), DOOR_RELAY, near=rig.base_pose(),
                      label=f"close {name}", hand=empty[0], body_free=TORSO)
    ctx = {}

    def no_park(diag):
        rig.log("close_no_park", name=name, q=round(q0, 4), ways=[(w[0], w[1]) for w in ways])
        return SkillFailure(f"close {name}: no base pose pushes the door shut or rides its handle shut")

    def found_park(found):
        kind, sd, _, way = ways[found.k]
        rig.log("close_park", park=[round(found.x, 3), round(found.y, 3), round(found.yaw, 1)], way=kind, side=sd,
                **({"grasp": way[0][0]} if way else {"above": ways[found.k][2]["above"]}))
        rig.caption = f"CLOSE {a['category']}: {'push the door' if kind == 'push' else 'go to handle'} ({sd} hand)"

    def ready(found):
        kind, sd, inp, way = ways[found.k]
        ctx.update(kind=kind, side=sd, q0=rig.joint(name), inp=inp)

        def rebuild(st, frm, prior):
            return build_at(st, found.k, prior, start=frm)

        hooks = {}
        if kind == "handle":
            t = way[1]

            def after_close(rig):
                f = np.asarray(rig.fingers(), float)[:2]
                if not handle_closed_on(f, t):
                    raise clearing(SkillFailure(f"close {name}: handle not grasped, fingers {f.round(4).tolist()}"),
                                   inp["pre_open"])
                rig._handle_grasp = {"name": name, "pre_open": inp["pre_open"], "q": rig.joint(name),
                                     "coll_kw": rig.kin.coll_kw, "side": "right"}
                rig.log("handle_grasped", name=name, fingers=f.round(4).tolist())

            def after_release(rig):
                rig._handle_grasp = None
            hooks = {"door_close_hand": {"after": after_close}, "door_release": {"after": after_release}}
        return found.plan, rebuild, hooks

    def failed(exc):
        if ctx.get("kind") == "handle" and getattr(rig, "_handle_grasp", None) is not None and \
                float(np.min(rig.fingers()[:2])) > HAND_OPENED_FRAC * ctx["inp"]["pre_open"]:
            rig._handle_grasp = None
        return None

    def done():
        q = rig.joint(name)
        rig.log("close_result", name=name, before=ctx["q0"], after=q, goal=goal, path=ctx["kind"], side=ctx["side"])
        tol = DOOR_OPEN_TOL if revolute else DOOR_CLOSED_TOL
        if abs(q - goal) >= tol:
            raise SkillFailure(f"close {name}: joint {ctx['q0']:.3f} -> {q:.3f}, goal {goal:.3f}")
        return q
    return Job(problem=problem, no_park=no_park, found=found_park, ready=ready, failed=failed, done=done)
