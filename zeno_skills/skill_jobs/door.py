"""Opening a door or a drawer by its handle (motion_skills.Job): the park search's problem -- every way
to hold the handle one goal -- the plan to run (skill_plans.plan_door), the result."""

from __future__ import annotations

import math
import numpy as np

from ..motion_state import clearing
from ..park_search import Problem
from ..rig import SkillFailure
from ..skill_plans import DOOR_RELAY
from ..skills import TCP_BACKOFF
from ..tolerances import (DOOR_OPEN_TOL, DRAWER_OPEN_FRAC, HAND_OPENED_FRAC, HANDLE_FINGER_MIN, HANDLE_GAP, RIDE_DONE_PRIS,
                          RIDE_DONE_REV, RIDE_OVERSHOOT)

VARIANT_COST = 0.05      # m of park cost per rank of a way to hold the handle (untilted side hook first)
RIDE_STEP_HINGE = 0.10   # rad between the ride's checked samples (skills._ride_check took 8 over the range; not measured)
RIDE_STEP_SLIDE = 0.03   # m ...on a slide
SIDE_TRACK = (0.03, 0.25)    # (lead, rate) of a side hook: the bar loaded through a finger (skills._ride's)
FRONT_TRACK = (0.01, 0.12)   # ...of a front pinch, held by friction only: gently


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
    approach, TCP_BACKOFF long; the ride to ``goal`` (RIDE_OVERSHOOT past it, done RIDE_DONE_REV / RIDE_DONE_PRIS short).
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
                "T_part_tcp": np.linalg.inv(pose(q0)) @ T, "u": R.T @ np.asarray(appr, float), "L": TCP_BACKOFF,
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
    if rig.held is not None or getattr(rig, "_handle_grasp", None) is not None:
        raise SkillFailure(f"open {name}: the right hand is not empty")
    goal = float(a["open_q"] if args.get("goal") is None else args["goal"])
    q0 = rig.joint(name)
    kin, base = rig.kin, RigBase(rig)
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

    problem = Problem(tuple(goals), build, DOOR_RELAY, near=rig.base_pose(), label=f"open {name}")
    ctx = {}

    def no_park(diag):
        rig.log("open_no_park", name=name, q=round(q0, 4), goal=round(goal, 4), ways=len(grips), diag=diag)
        return SkillFailure(f"open {name}: no base pose can grasp the handle and ride the motion")

    def found_park(found):
        grasp, flip, tilt = grips[found.k][1]
        rig.log("open_park", park=[round(found.x, 3), round(found.y, 3), round(found.yaw, 1)],
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
            f = np.asarray(rig.fingers(), float)[:2]
            if not handle_closed_on(f, t):
                raise clearing(SkillFailure(f"open {name}: handle not grasped, fingers {f.round(4).tolist()}"),
                               grip["pre_open"])
            rig._handle_grasp = {"name": name, "pre_open": grip["pre_open"], "q": rig.joint(name),
                                 "coll_kw": rig.kin.coll_kw}
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
        if getattr(rig, "_handle_grasp", None) is not None and float(np.min(rig.fingers()[:2])) > HAND_OPENED_FRAC * ctx["grip"]["pre_open"]:
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
