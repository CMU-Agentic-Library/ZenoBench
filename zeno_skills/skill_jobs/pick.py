"""The pinch pick's job (motion_skills.Job): the park search's problem, the plan to run after the drive, the result."""

from __future__ import annotations

import math
import numpy as np

from ..annotations import opening
from ..motion_state import Aim, aim_pose, clearing
from ..park_search import VARIANT_COST, Problem
from ..rig import Dropped
from ..primitives import turn
from ..rig import SkillFailure
from ..run import observe
from ..sticky import note_grasp
from ..skill_plans import FREE_HAND, PICK_RELAY
from ..tolerances import FLOOR_Z, GRIP_CLOSED_BY, SHUT, TARGET_TOL
from .door_access import door_ahead, front_of, outward
from ..skills import (APPROACH_STEP, PICK_LEAVE_CHECK, PINCH_KINDS, _carry_goal_set, _grasp_approach, _grasp_of, _pick_judged, _pinch_candidates, _surface_under, _watching, check_held, edge_held)


PICK_CAND_COST = 0.05          # m of park cost per rank of a grasp candidate (their order: centre, nearest first)


def _pick_problem(rig, name, cands, T_obj, near, prefer=(), build_with=None, relay_free=None, sides=("right",)):
    """The park of the pick of ``name`` (its box frame at T_obj, the State's): every grasp candidate with
    every hand of ``sides`` (the empty ones: HAND_PLAN 9c) is one goal (its reach-in's start, the grasp, the
    first of the lift as the points the arm must reach; the reach-in's start as the relay pose the ranking
    solves; the hand), and a park counts when the whole pick plans from it (``build_with``: the catalog's
    builder, skill_plans.plan_pick, that hand's kinematics, from the posture the arm arrives in -- run_skill
    sets it from the catalog -- the hand opened to the candidate's width; the grasp in the object's frame,
    _grasp_of).  A hand later in ``sides`` costs VARIANT_COST more (the right first, a weak preference: the
    ranking's score decides -- not the right tried first, then the left).  ``near`` / ``prefer`` as Problem's
    (in front of a door's free edge: door_access.front_of).  (Problem, {side: carry goal set}, the grasps)."""
    build_with = build_with or _plan_pick()
    carry_goals = {sd: _carry_goal_set(rig, name, side=sd) for sd in sides}
    grasps = [_grasp_of(name, g, T_obj) for g in cands]
    goals, which = [], []
    for j, sd in enumerate(sides):
        for i, g in enumerate(cands):
            u, L = _grasp_approach(g)
            start = np.asarray(g["p"], float) - L * np.asarray(u, float) / np.linalg.norm(u)
            goals.append(((start, np.asarray(g["p"], float), np.asarray(g["p"], float) + [0, 0, PICK_LEAVE_CHECK]),
                          (start, np.asarray(g["R"], float)), PICK_CAND_COST * i + VARIANT_COST * j, sd))
            which.append(i)

    def build(s, k, prior):
        sd = goals[k][3]
        return build_with(_kin(rig, sd), s, grasps[which[k]], carry_goals[sd], prior=prior, step=APPROACH_STEP)

    problem = Problem(tuple(goals), build, PICK_RELAY, near=near, prefer=tuple(prefer), relay_free=relay_free,
                      label=f"pick {name}", hand=sides[0])
    return problem, carry_goals, grasps, which


def _kin(rig, side):
    """``side``'s arm kinematics (Rig.arm_kin; the tests' stand-ins have kin / left_kin)."""
    return rig.kin if side == "right" else rig.left_kin


def _plan_pick():
    from ..skill_plans import plan_pick
    return plan_pick


def _pick_ready(rig, name, g, grasp, plan, carry_goals, out, plan_pick=None, side="right"):
    """The pick's plan to run from the park (the park search's: a grasp the object no longer gives
    has run build it again, primitives.holds), its builder for the rest, its hooks (run.run).  Between the
    segments the pick's own steps: the object watched on the way in, the reach checked, the pinch
    judged and the load registered as held (``out["tcp0"]``: the TCP where the hand closed), the
    carry checked.  ``grasp``: plan_pick's (_grasp_of), ``g`` the candidate it came from; ``side`` the hand
    (HAND_PLAN 9c), ``carry_goals`` that hand's."""
    from ..rig import _chain_cmd, _chain_q, _fingers_of
    kin = _kin(rig, side)
    plan_pick = plan_pick or _plan_pick()

    def rebuild(state, frm, prior):
        return plan_pick(kin, state, grasp, carry_goals, start=frm, prior=prior, step=APPROACH_STEP)

    def after_grasp(rig):
        # the hand against where the reach-in sent it (Rig._settle measured it as the reach-in stopped; run
        # judges every segment by the same, after this hook): whether the grasp is still the object's was
        # checked before the reach-in ran (primitives.holds)
        err = rig.last_off
        if kin.motion is not None:
            # what the open hand at the commanded grasp pose penetrates in the full model (grasp_contacts)
            rig.log("grasp_contacts", obj=name, kind=g["kind"], tcp_err_m=round(err, 4),
                    hits=kin.motion.contacts_by_owner(kin, _chain_cmd(rig, side), kin._other_q()))
        if err > TARGET_TOL:
            # stopped short of the grasp pose: something is in the way, closing here pinches elsewhere
            rig.log("pick_result", obj=name, kind=g["kind"], tcp_err_m=round(err, 4), held=False, why="blocked")
            rig.focus_z = None
            # out of the contact straight up: the failure exit run makes (skill_plans.plan_clear)
            raise clearing(SkillFailure(f"pick {name}: the open hand stopped {err:.3f} m short of the grasp pose"))

    def before_close(rig):
        rig.caption = f"PICK {name}: close gripper"
        if kin.motion is not None and kin.motion.by_owner.get(f"object:{name}"):
            out["T_obj0"], out["q_grasp"] = kin.motion.object_frames()[name], _chain_cmd(rig, side)

    def after_close(rig):
        f = _fingers_of(rig, side)
        if not np.all((f[:2] > SHUT) & (f[:2] < float(g["pre_open"]) - GRIP_CLOSED_BY)):
            # not pinched: shut on nothing, or a finger left where it opened (it met nothing).  Leave
            # with an open hand clear of the neighbours; nothing is held, so nothing is welded
            rig.log("pick_result", obj=name, kind=g["kind"], fingers=f.round(4).tolist(), held=False,
                    why="not pinched")
            rig.focus_z = None
            # the hand opened and out of the contact: the failure exit run makes (plan_clear)
            raise clearing(SkillFailure(f"pick {name}: not held (fingers {np.round(f[:2], 4).tolist()}, "
                                        f"opened to {g['pre_open']:.3f})"), 0.04)
        # held from here (and welded, under sticky hands): the hand's pose as it stands
        tcp0, R = kin.tcp(_chain_q(rig, side))
        held = {"name": name, "kind": "pinch", "tcp_minus_body": tcp0 - rig.obj_pose(name)[0], "R": R,
                "pre_open": g["pre_open"]}
        if g["kind"] == "thickness_pinch":
            # a flat object held at a side: what placing it flat needs (kind "edge", skill_jobs.place._edge_goals)
            held.update(edge_held(rig, name, tcp0, R))
        setattr(rig, "held" if side == "right" else "left_held", held)
        out["tcp0"] = tcp0
        if "T_obj0" in out:
            # the hold a plan assumes (the load where it stood, the hand where it closed) against the
            # hold measured now: what skill_plans.HELD_POSE_MARGIN stands for
            rig.sync_world()
            p_g, R_g = kin.tcp(out["q_grasp"])
            T_g = np.eye(4)
            T_g[:3, :3], T_g[:3, 3] = R_g, p_g
            planned = np.linalg.inv(T_g) @ out["T_obj0"]
            measured = kin.motion.held_in_tcp(kin, _chain_q(rig, side), name)   # as the State has it (Rig.snapshot)
            rig.log("held_offset", obj=name, kind=g["kind"],
                    offset_m=round(float(np.linalg.norm(measured[:3, 3] - planned[:3, 3])), 4),
                    turn_deg=round(math.degrees(turn(planned[:3, :3], measured[:3, :3])), 2))
        rig.caption = f"PICK {name}: lift"

    watch = lambda: _watching(rig, name)
    hooks = {"pick_reach": {"around": watch}, "pick_grasp": {"around": watch, "after": after_grasp},
             "pick_close": {"before": before_close, "after": after_close},
             "carry_in": {"after": lambda rig: check_held(rig, "carry_in", open_hand=False, side=side)}}
    return plan, rebuild, hooks


def pick_hands(rig, name, hand=None):
    """The hands a pick of ``name`` may use (HAND_PLAN 9c): the empty ones, the right first; ``hand`` (the
    route's: a task that keeps the other hand for something else) only that one; ZENO_PICK_SIDE a diagnostic
    switch (as ZENO_OPEN_SIDE), not for the baseline.  SkillFailure when none is free."""
    import os
    want = hand or os.environ.get("ZENO_PICK_SIDE") or None
    empty = [sd for sd in ("right", "left") if (rig.held if sd == "right" else getattr(rig, "left_held", None)) is None]
    sides = [sd for sd in empty if want in (None, "any", sd)]
    if not sides:
        raise SkillFailure(f"pick {name}: no empty hand" + (f" ({want} asked)" if want else ""))
    return tuple(sides)


def pick_job(rig, args, state, skill=None):
    """motion_skills.Job of the pinch pick: every grasp candidate one goal of the park search (the
    whole pick planned there, skill_plans.plan_pick, the grasp in the object's frame); after the drive
    the plan run with the pick's hooks (run builds it again when the object no longer gives its
    grasp: primitives.holds); then judged (_pick_judged)."""
    from ..motion_skills import Job
    name, max_candidates, kinds = args["name"], args.get("max_candidates", 12), args.get("kinds", PINCH_KINDS)
    obj = rig.ann.objects[name]
    pos, quat = rig.obj_pose(name)
    st = rig.state()
    floor_z = float(rig.geo.bottom(name, st)[2])
    surface_z = _surface_under(rig, name, st)
    cands, extra = _pinch_candidates(rig, obj, pos, quat, kinds, surface_z)
    if not cands:
        raise SkillFailure(f"pick {name}: no pinch grasp annotated")
    # the grasps in the object's box frame as the State has it (the plan derives them from there)
    T_obj = (getattr(state, "objects", None) or {}).get(name)
    if T_obj is None:
        raise SkillFailure(f"pick {name}: not in the collision model")
    rig.sync_world()
    rig.focus_z = float(pos[2])
    bx, by, _ = rig.base_pose()
    # behind a door (a cavity it stands in, a shelf of the articulated): the robot's pose after
    # opening it biases the search toward the hinge, so a park in front of the door's free edge is
    # tried first (door_access.front_of, from the annotation: no scene's coordinates written here), and the
    # grasps most outward (toward the opening) first
    door = door_ahead(rig, rig.geo.support_under(name, st), pos, f"pick {name}")
    near, prefer = rig.base_pose(), ()
    if door is not None:
        out = opening(door)
        prefer, near = (front_of(rig, door, pos),), rig.base_pose()[:2]
        across = np.array([-out[1], out[0]])
        cands.sort(key=lambda g: (-outward(door, g["p"]), -g.get("tilt", 0),
                                  abs(float((np.asarray(g["p"])[:2] - np.asarray(pos)[:2]) @ across))))
    else:
        # off-centre pinch points of a long object let it swing in the hand:
        # prefer the centre, use the others when it is out of reach
        cands.sort(key=lambda g: np.linalg.norm(g["p"][:2] - np.array([bx, by])) + 0.3 * g.get("along_rank", 0))
    # every grasp candidate is one goal of the park search (park_search.find_park), and a park is
    # one where the whole pick can be planned (skill_plans.plan_pick) -- that plan is run
    goal_cands = cands[:max_candidates] + extra
    build_with = skill.build if skill is not None else None
    sides = pick_hands(rig, name, args.get("hand"))
    # behind a door: the parks whose ranking solution of the reach-in start is free first (Problem.relay_free)
    problem, carry_goals, grasps, which = _pick_problem(rig, name, goal_cands, T_obj, near, prefer, build_with,
                                                        relay_free=FREE_HAND if door is not None else None,
                                                        sides=sides)
    ctx = {"out": {}}

    def no_park(diag):
        getattr(rig, "log", lambda *a, **k: None)("pick_no_park", obj=name, pos=[round(float(v), 3) for v in pos],
                quat=[round(float(v), 3) for v in quat], n_cands=len(cands), diag=diag)
        return SkillFailure(f"pick {name}: no reachable grasp from any base pose")

    def found_park(found):
        g = goal_cands[which[found.k]]
        rig.log("pick_park", obj=name, kind=g["kind"], hand=problem.side(found.k),
                park=[round(found.x, 3), round(found.y, 3), round(found.yaw, 1)], floor=bool(floor_z < FLOOR_Z))
        rig.caption = f"PICK {name}: approach" + (" (torso down: floor)" if floor_z < FLOOR_Z else "")

    def ready(found):
        # after the drive: the candidate's grasp on the object where it stands now (the drive may
        # have knocked it) -- the plan checks the same against the State (primitives.holds) and is
        # built again from there when it is off
        g, grasp, side = goal_cands[which[found.k]], grasps[which[found.k]], problem.side(found.k)
        p_now, q_now = rig.obj_pose(name)
        now = aim_pose(observe(rig), Aim(name, grasp["T_obj_tcp"], side=side))
        if now is None:
            raise SkillFailure(f"pick {name}: not in the collision model")
        rig.log("pick_target", obj=name, pos=[round(float(v), 3) for v in p_now],
                quat=[round(float(v), 3) for v in q_now], p=[round(float(v), 3) for v in now[0]],
                kind=g["kind"], azimuth=g.get("azimuth"), tilt=g.get("tilt"))
        note_grasp(rig, name, now[0], now[1], "edge" if g["kind"] == "thickness_pinch" else "pinch", g["pre_open"])
        ctx["g"], ctx["pos"], ctx["side"] = g, p_now, side
        return _pick_ready(rig, name, g, grasp, found.plan, carry_goals[side], ctx["out"], build_with, side)

    def failed(exc):
        if isinstance(exc, Dropped):
            return SkillFailure(f"pick {name}: not held ({exc})")
        return None

    def done():
        return _pick_judged(rig, name, ctx["g"], ctx["out"]["tcp0"], ctx["pos"], ctx["side"])
    return Job(problem=problem, no_park=no_park, found=found_park, ready=ready, failed=failed, done=done)
