"""An object pushed or dragged across its support (motion_skills.Job, the catalog's "push": docs/MOTION_ARCHITECTURE.md
section 6, contact): one leg -- every way to touch it (each direction it may go; a push from behind it or a drag
pressing on its top; each with the closed fingers turned four ways) one goal of the park search, the whole leg
planned there as far as the arm reaches (skill_plans.plan_slide) -- and ``push_object``, the legs of a longer
push, each from where the last left the object (a task-level loop: docs 6, contact skills over several parks)."""

from __future__ import annotations

import numpy as np

from ..kinematics import PAD_HALF_WIDTH, PAD_THICKNESS, PAD_TIP, finger_model_box, gripper_rot
from ..park_search import VARIANT_COST, Problem
from ..rig import SkillFailure
from ..skill_plans import SLIDE_RELAY, SLIDE_STEP, slide_travel
from ..tolerances import (DRAG_PRESS, DRAG_RIM, DRAG_SKID, LEAVE_MARGIN, PUSH_DONE_TOL, PUSH_MOVED_MIN, SLIDE_GAP,
                          SLIDE_PAD_GAP)

MODES = ("push", "drag")  # the ways to move it, the order a caller prefers them in by default


def _reach_along(R, n, box):
    """m the closed fingers reach from the TCP along the horizontal ``n`` with the gripper turned R, the
    fingers the box (half width across the closing plane, inner face, outer face, tip below the TCP)."""
    half_w, y_in, y_out, tip = box
    corners = np.array([[sx * half_w, sy * t, -z] for sx in (-1, 1) for sy in (-1, 1) for t in (y_in, y_out)
                        for z in (0.0, tip)])
    return float(np.max(corners @ np.asarray(R, float).T @ np.r_[n, 0.0]))


def _fingers_along(R, n):
    """...the planner's fingers (its finger box: kinematics.finger_model_box, what the plan checks)."""
    return _reach_along(R, n, finger_model_box())


def _pads_along(R, n):
    """...the real pads (kinematics' pad box, which the finger box holds)."""
    return _reach_along(R, n, (PAD_HALF_WIDTH, 0.0, PAD_THICKNESS, PAD_TIP))


def slide_ways(rig, name, T_obj, n, d, modes=MODES):
    """plan_slide's push per way to touch ``name`` to move it ``d`` along the horizontal unit ``n``
    (skills' old push: a push from behind with the closed fingertips just above the surface it rests
    on, a drag pressing on its top near the leading rim; the fingers closing across n, the other way
    across, along n, against n), mode by mode in the order of ``modes``.  The push point in the
    object's box frame as the State has it (the plan derives it from there: ``T_obj``, that frame in
    the State).  The entry by a pick's rule (docs/COLLISION_PLAN.md 2): the hand comes down
    pick_approach() -- the fingers are what reaches in, their length and LEAVE_MARGIN -- landing a push
    LEAVE_MARGIN behind the push point.  The hand runs ``lag`` before the object moves (primitives.Pushed):
    a push's SLIDE_GAP and the planner's finger box beyond the real pads along n (2.7 / 4.2 mm, by the
    turn), a drag's DRAG_SKID; it runs d + lag at most, and the leg must move the object at least
    min(d, PUSH_MOVED_MIN).  [(mode, rank of the turn, push)]."""
    from ..skills import _half_along, _pads_clear_of, _perp, _surface_under, _yaw, pick_approach
    st = rig.state()
    size = rig.ann.asset_of(rig.ann.objects[name])["size"]
    b = rig.geo.bottom(name, st)
    h = _half_along(size, _yaw(st["objects"][name]["quat"]), n)
    floor = _surface_under(rig, name, st)          # the surface the pads clear: a pick's (_surface_under)
    lat = _perp(n)
    above, least = pick_approach(), min(float(d), PUSH_MOVED_MIN[0])
    out = []
    for m in modes:
        for i, c in enumerate((lat, -lat, n, -n)):
            R = gripper_rot([0, 0, -1.0], [c[0], c[1], 0.0])
            if m == "push":
                # the closed fingers SLIDE_GAP off the back face, SLIDE_PAD_GAP above that surface (_pads_clear_of)
                fingers = _fingers_along(R, n)
                xy = b[:2] - n * (h + fingers + SLIDE_GAP)
                p = _pads_clear_of({"pre_open": 0.0, "R": R, "p": np.r_[xy, floor]}, floor, SLIDE_PAD_GAP)
                lag = SLIDE_GAP + fingers - _pads_along(R, n)
                way = {"back": LEAVE_MARGIN, "above": above}
            else:
                xy = b[:2] + n * max(0.0, h - DRAG_RIM)
                p = np.r_[xy, b[2] + size[2] + DRAG_PRESS]
                lag = DRAG_SKID
                way = {"back": 0.0, "above": above}
            W = np.eye(4)
            W[:3, :3], W[:3, 3] = R, p
            out.append((m, i, {"obj": name, "T_obj_tcp": np.linalg.inv(T_obj) @ W, "n": np.r_[n, 0.0],
                               "d": float(d) + lag, "lag": lag, "least": least, **way}))
    return out


def slide_job(rig, args, state, skill=None):
    """motion_skills.Job of one leg: ``args`` {name, support (the annotated support it rests on), dirs
    [(n: a horizontal unit, d: m it is still to go that way, cost: m -- what going that way costs)],
    modes (the ways, preferred first; default MODES), label}.  Every way to touch it in every direction
    one goal of the park search (the whole leg planned there: skill_plans.plan_slide, the right hand):
    the goal's cost is its direction's plus VARIANT_COST per rank of the turn, and every way of a mode
    comes before any of the next (Problem.tiers).  The leg goes as far as the arm gets from the park
    (plan_slide measures it); the ranking solves the push's end, and where no park reaches any end, how
    far along each one gets (Problem.relay_from).  Run with its captions; the result is (which of
    ``dirs`` it went, the travel measured along it, the travel the plan predicted)."""
    from ..motion_skills import Job
    from ..skills import ContactUnreachable
    name, support, label = args["name"], args["support"], args.get("label", "PUSH")
    modes = tuple(args.get("modes") or MODES)
    dirs = [(np.asarray(n, float)[:2], float(d), float(cost)) for n, d, cost in args["dirs"]]
    if rig.held is not None:
        raise SkillFailure(f"push {name}: the right hand must be empty")
    T_obj = (getattr(state, "objects", None) or {}).get(name)
    if T_obj is None:
        raise SkillFailure(f"push {name}: not in the collision model")
    rig.sync_world()
    kin = rig.kin
    rests = (kin.rest, kin.drive)
    build_with = skill.build if skill is not None else None
    if build_with is None:
        from ..skill_plans import plan_slide as build_with
    ways, goals, tiers, starts = [], [], [], []      # ways[k] = (index into dirs, mode, push)
    for j, (n, d, cost) in enumerate(dirs):
        for m, i, push in slide_ways(rig, name, T_obj, n, d, modes):
            T = np.asarray(T_obj, float) @ push["T_obj_tcp"]
            p, R = T[:3, 3], T[:3, :3]
            land = p - push["back"] * push["n"]
            top = land + [0.0, 0.0, push["above"]]
            end = p + push["d"] * push["n"]           # the relay: the push's end (skill_plans.SLIDE_RELAY) ...
            ways.append((j, m, push))
            goals.append(((top, p, end), (end, R), cost + VARIANT_COST * i))
            tiers.append(modes.index(m))
            starts.append(p)                          # ... reached from the push point: a leg may stop short

    def build(s, k, prior):
        return build_with(kin, s, ways[k][2], rests, prior=prior)

    # every way of a mode before any of the next (Problem.tiers): one search over pushes and drags ranked by
    # the arm's manipulability chose a drag where a push would do, and a drag threw the object (T01
    # paperback 4.5 cm asked, 40 cm moved; T29 table_book, 11-12); VARIANT_COST alone is a weak preference
    problem = Problem(tuple(goals), build, SLIDE_RELAY, near=rig.base_pose(), label=f"{label.lower()} {name}",
                      tiers=tuple(tiers), relay_from=tuple(starts), reach_step=SLIDE_STEP)
    ctx = {"b0": np.asarray(rig.geo.bottom(name, rig.state()), float)}

    def no_park(diag):
        rig.log("push_no_park", obj=name, dirs=[np.round(n, 3).tolist() for n, _, _ in dirs],
                d=[round(d, 3) for _, d, _ in dirs], modes=list(modes), diag=diag)
        return ContactUnreachable(f"push {name}: no base pose reaches a {' or a '.join(modes)} "
                                  f"clear of its neighbours")

    def found_park(found):
        j, m, _ = ways[found.k]
        ctx["j"], ctx["mode"], ctx["planned"] = j, m, slide_travel(found.plan) or 0.0
        rig.log("push_park", obj=name, mode=m, dir=np.round(dirs[j][0], 3).tolist(), d=round(dirs[j][1], 3),
                leg=round(ctx["planned"], 3), park=[round(found.x, 3), round(found.y, 3), round(found.yaw, 1)])
        rig.caption = f"{label} {name}: " + ("go behind it" if m == "push" else "press on it to drag")
        rig.focus_z = float(support["z"])

    def ready(found):
        push = ways[found.k][2]

        def rebuild(st, frm, prior):
            return build_with(kin, st, push, rests, start=frm, prior=prior)

        def before_push(rig):
            rig.caption = f"{label} {name}: " + ("slide along the surface" if ctx["mode"] == "push" else "drag it along")
        return found.plan, rebuild, {"slide_push": {"before": before_push}}

    def done():
        rig.focus_z = None
        b = np.asarray(rig.geo.bottom(name, rig.state()), float)
        return ctx["j"], float(dirs[ctx["j"]][0] @ (b[:2] - ctx["b0"][:2])), ctx["planned"]
    return Job(problem=problem, no_park=no_park, found=found_park, ready=ready, done=done)


def push_object(rig, name, s, ways, label="PUSH", modes=MODES):
    """``name`` slid across its support ``s`` along one of ``ways`` [(n: a horizontal unit, distance: m,
    enough: m or None)] by the ways of ``modes`` (preferred first): the catalog's "push" (slide_job) leg
    by leg, each from where the last left it and as far as the arm gets from its park -- no set length
    (docs/COLLISION_PLAN.md 2: the park that pushes farthest, until it reaches no further, then the next
    park).  The first leg's one park search has every direction as goals (its cost: its distance --
    docs 7: every way of the task a goal, no search per direction and none after a failure); the
    direction it went is kept for the rest.  It stops once the object is within PUSH_DONE_TOL of the
    distance or has moved ``enough`` (every extra leg parks next to an object that may already
    overhang); a leg that moved it less than PUSH_MOVED_MIN (of what the leg's plan predicted) fails.
    (the direction n it went, the distance moved along it, measured)."""
    from ..motion_skills import SKILLS, run_skill
    modes = tuple(modes)
    if not modes or any(m not in MODES for m in modes):
        raise ValueError(f"unknown contact mode: {modes}")
    least, frac = PUSH_MOVED_MIN
    ways = [(np.asarray(n, float)[:2], float(dist), enough) for n, dist, enough in ways]
    b0 = np.asarray(rig.geo.bottom(name, rig.state()), float)
    went, moved = None, 0.0
    while True:
        todo = [w for w in (ways if went is None else [went])
                if moved < w[1] - PUSH_DONE_TOL and (w[2] is None or moved < w[2])]
        if not todo:
            break
        dirs = [(n, dist - moved, dist) for n, dist, _ in todo]
        j, step_moved, planned = run_skill(rig, SKILLS["push"], {"name": name, "support": s, "dirs": dirs,
                                                                 "modes": modes, "label": label})
        went = todo[j]
        b = np.asarray(rig.geo.bottom(name, rig.state()), float)
        moved = float(went[0] @ (b[:2] - b0[:2]))
        rig.log("push_result", obj=name, dir=np.round(went[0], 3).tolist(), moved=round(step_moved, 3),
                planned=round(planned, 3), total=round(moved, 3))
        if step_moved < min(least, frac * planned):
            raise SkillFailure(f"push {name}: object did not move")
    return (ways[0][0] if went is None else went[0]), moved
