"""The set-down's job (motion_skills.Job): the carry posture first, the park search's problem, the plan to run after the drive, the result."""

from __future__ import annotations

import math
import numpy as np

from ..annotations import rz
from ..evaluator import quat_R
from ..park_search import Problem
from ..rig import FREE_SPACE_KW
from ..rig import LEAVE_GAP
from ..rig import SkillFailure
from ..primitives import query
from ..run import observe
from ..skill_plans import FREE_HAND, PLACE_RELAY, T_of
from ..sticky import rest_R
from ..skills import (APPROACH_STEP, PICK_REACH_TOL, PLACE_LEVEL_MIN, PLACE_SPOT_COST, PLACE_TILTED_COST, PLACE_YAWS, PLACE_YAW_COST, _lowest_z, check_held, pick_approach)
from .carry import _carry_bottom_z, carry_posture


def place_job(rig, args, state, skill=None):
    """motion_skills.Job of the set-down: the carry posture settled for the support's rim first
    (carry_posture), every spot x hold x wrist turn one goal of the park search (the whole place
    planned there, skill_plans.plan_place, the goal the object's pose); after the drive the plan run
    with the place's hooks (run builds it again when the hold no longer gives its set-down pose:
    primitives.holds); then the result judged."""
    from ..motion_skills import Job
    name, s, spots, tray = args["name"], args["support"], args["spots"], args.get("tray")
    kin = rig.kin
    plan_place = skill.build if skill is not None else _plan_place()
    asset = rig.ann.asset_of(rig.ann.objects[name])
    # the carry posture of the drive to the park, before the park search checks it there
    clear_z = _carry_bottom_z(rig, tray or s["name"])
    carry_bottom_z = max(s["z"] + 0.03, clear_z or 0.0)
    carry_posture(rig, min_bottom_z=carry_bottom_z)
    rig.sync_world()
    # how the hand holds it: as it hangs, and levelled (tilted more than PLACE_LEVEL_MIN; preferred,
    # 2026-11-03: either is allowed).  Per relation: TCP minus the object's origin (world frame),
    # the TCP rotation, how far the origin stands above the object's lowest point.  The TCP is the
    # measured one (rig.q()), as in the State's hold (Rig.snapshot): the two must agree, or the arm's
    # sag under the load (q - q_cmd up to 0.013 rad, 11-08) reads as a shifted hold
    st = rig.state()
    p_obj, q_obj = rig.obj_pose(name)
    p_obj = np.asarray(p_obj, float)
    R_obj = quat_R(q_obj)
    tcp, R_tcp = kin.tcp(rig.q())
    relations = [(tcp - p_obj, R_tcp, None, float(p_obj[2] - _lowest_z(rig, name, st)))]
    over = math.degrees(math.acos(max(-1.0, min(1.0, float(R_obj[2, 2])))))
    if rig.held["kind"] != "corner" and over > PLACE_LEVEL_MIN:
        R_lvl = rest_R(q_obj) @ R_obj.T
        relations.insert(0, (R_lvl @ (tcp - p_obj), R_lvl @ R_tcp, round(over, 1),
                             -float(asset["origin_to_bottom_center"][2])))
    search_near = rig.base_pose()
    if math.hypot(search_near[0] - spots[0][0], search_near[1] - spots[0][1]) > 1.0:
        # far from the target: rank parks by reach to the target, not by
        # distance from here (all tries were spent near a corner 1.4 m away)
        search_near = None
    # the set-down poses (the relay pose): every spot, relation and wrist turn is one goal
    goals, leg_sets, cost = [], [], []
    for rank, spot in enumerate(spots):
        for off0, R0, levelled, hang in relations:
            body = np.array([spot[0], spot[1], s["z"] + hang + LEAVE_GAP])
            for deg in PLACE_YAWS:
                Rz = rz(math.radians(deg))
                goals.append((spot, Rz @ R0, levelled, deg, hang))
                leg_sets.append([(body + Rz @ off0, Rz @ R0, FREE_SPACE_KW)])
                cost.append(PLACE_SPOT_COST * rank + PLACE_YAW_COST * abs(deg) / 45.0 +
                            (PLACE_TILTED_COST if levelled is None and len(relations) > 1 else 0.0))
    open_w = float(rig.held.get("pre_open", 0.04))
    rests = (kin.rest, kin.drive)
    # what plan_place takes: the pose of the object's box frame each set-down pose puts it at,
    # through the hold the State has now (the plan derives the TCP back from the hold it is built
    # with: the same pose while the hold is the same, the object at its pose when it turned)
    held = observe(rig).held(kin.side)
    T_hold = np.eye(4) if held is None else np.asarray(held.T_tcp_obj, float)
    targets = [T_of(ls[0][1], ls[0][0]) @ T_hold for ls in leg_sets]

    # every set-down pose is one goal of the park search (park_search.find_park), and a park is one
    # where the whole place can be planned (skill_plans.plan_place) -- that plan is run
    def build(st, k, prior):
        return plan_place(kin, st, targets[k], open_w, pick_approach(), rests, prior=prior, step=APPROACH_STEP,
                          obj=name)
    problem = Problem(tuple(((ls[0][0],), (ls[0][0], ls[0][1]), c) for ls, c in zip(leg_sets, cost)), build,
                      PLACE_RELAY, near=search_near, label=f"place {name}")
    ctx = {}

    def no_park(diag):
        return SkillFailure(f"place {name}: no spot of {len(spots)} on {s['name']} reachable "
                            f"({len(leg_sets)} goals; rejected: { {k: v for k, v in diag.items() if v} })")

    def found_park(found):
        spot, R, levelled, deg, hang = goals[found.k]
        plan = found.plan
        reach = None if plan is None else next((sg for sg in plan.segments if sg.name == "place_reach"), None)
        L = None if reach is None else reach.info.get("set_down_m")
        rig.log("place_park", obj=name, park=[round(found.x, 3), round(found.y, 3), round(found.yaw, 1)],
                spot=[round(v, 3) for v in spot], yaw_deg=deg, levelled=levelled, goals=len(leg_sets),
                set_down_m=None if L is None else round(L, 4))
        rig.caption = f"PLACE {name}: carry"
        rig.focus_z = s["z"]

    def ready(found):
        # arrived with the load above the target surface (Job.travel: the carry posture's
        # min_bottom_z).  Without a weld the object may have turned in the pinch on the way (bowls
        # held at the rim, spoons): the plan's set-down checks its pose against the hold the State
        # has now (primitives.holds) and is built again from there when it is off
        ctx["spot"] = goals[found.k][0]
        ctx["kind"] = rig.held["kind"]
        return _place_ready(rig, name, s, targets[found.k], open_w, found.plan, plan_place)

    def done():
        return _place_result(rig, name, s, ctx["spot"], ctx["kind"], tray)
    # the drive keeps the posture carry_posture settled above: it does not try the higher ride again
    return Job(problem=problem, no_park=no_park, found=found_park,
               travel={"min_bottom_z": carry_bottom_z, "raise_load": False},
               ready=ready, done=done)


def _plan_place():
    from ..skill_plans import plan_place
    return plan_place


def _place_ready(rig, name, s, goal, open_w, plan, plan_place=None):
    """The place's plan to run (run.run) to set ``name`` down with its box frame at ``goal`` (the
    park search's plan: a set-down pose the hold no longer gives has run build it again,
    primitives.holds), its builder for the rest, its hooks.  Between the segments the place's own steps:
    the reach checked, the release logged and the load no longer held."""
    kin = rig.kin
    plan_place = plan_place or _plan_place()
    out_len, rests = pick_approach(), (kin.rest, kin.drive)

    def rebuild(state, frm, prior):
        return plan_place(kin, state, goal, open_w, out_len, rests, start=frm, prior=prior, step=APPROACH_STEP,
                          obj=name)

    def before_pull_out(rig):
        # let go, it may have settled against a finger: allowed on the pull-out, recorded -- a query
        # of the State now with the fingers in the model (primitives.query), nothing changed
        st = observe(rig)
        with query(kin, st, FREE_HAND):
            if kin.scene is not None and not kin.free(st.q(kin.side)):
                rig.log("place_pull_out_touching", obj=name, why=kin.explain(st.q(kin.side)))

    def after_down(rig):
        # the hand against where the set-down sent it (its end, the command now): whether the hold
        # still gives that pose was checked before the set-down ran (primitives.holds, PLACE_TOL)
        err = float(np.linalg.norm(kin.tcp(rig.q())[0] - kin.tcp(rig.q_cmd)[0]))
        if err > PICK_REACH_TOL:
            # the set-down is checked free all the way: stopped short, something is in the way
            raise SkillFailure(f"place {name}: the set-down stopped {err:.3f} m short of its pose")
        check_held(rig, "place_down", open_hand=False)
        rig.caption = f"PLACE {name}: release"
        before_release, _ = rig.obj_pose(name)
        rig.log("place_before_release", obj=name, pos=np.round(before_release, 4).tolist(),
                gap_m=round(float(_lowest_z(rig, name, rig.state())) - float(s["z"]), 4))

    def after_release(rig):
        after_open, _ = rig.obj_pose(name)
        rig.log("place_after_open", obj=name, pos=np.round(after_open, 4).tolist())
        rig.held = None

    def set_down_caption(rig):
        rig.caption = f"PLACE {name}: set down"

    hooks = {"place_reach": {"before": set_down_caption}, "place_down": {"after": after_down},
             "place_release": {"after": after_release}, "place_pull_out": {"before": before_pull_out}}
    return plan, rebuild, hooks


def _place_result(rig, name, s, spot, kind, tray):
    """Did the set-down leave ``name`` on ``s`` near ``spot`` (or inside the tray)?  SkillFailure when not.
    (The 90 ticks it settles first are the plan's last segment, place_settle.)"""
    rig.focus_z = None
    st = rig.state()
    if tray is not None:
        ok, why = rig.geo.inside(name, tray, st)
        rig.log("place_result", obj=name, container=tray, inside=bool(ok), detail=why)
        if not ok:
            raise SkillFailure(f"place {name} in {tray}: {why}")
        return True
    b = rig.geo.bottom(name, st)
    err = float(np.linalg.norm(b[:2] - np.asarray(spot)))
    on, why = rig.geo.on(name, s["name"], st)
    rig.log("place_result", obj=name, support=s["name"], xy_err_m=round(err, 4), on_support=bool(on))
    if not on:
        # what is it resting on: the objects next to it
        near = {o: [round(float(v), 3) for v in st["objects"][o]["pos"]] for o in rig.ann.objects
                if o != name and o in st["objects"] and
                np.linalg.norm(np.asarray(st["objects"][o]["pos"][:2]) - b[:2]) < 0.30}
        rig.log("place_not_on_support", obj=name, bottom=[round(float(v), 3) for v in b],
                quat=[round(float(v), 3) for v in st["objects"][name]["quat"]], near=near)
    tol = 0.12 if kind == "corner" else 0.10   # a corner-held object pivots flat on release
    if not (on and err < tol):
        raise SkillFailure(f"place {name}: xy err {err:.3f} m, on support {on} ({why})")
    return True
