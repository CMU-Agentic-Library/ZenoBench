"""The pinch pick's job (motion_skills.Job): the park search's problem, the plan to run after the drive, the result."""

from __future__ import annotations

import math
import numpy as np

from ..clearance import LEAVE_CONTACT
from ..motion_state import Failure
from ..motion_state import with_width
from ..park_search import Problem
from ..rig import Dropped
from ..rig import HINT_REACH
from ..rig import HINT_TURN
from ..rig import SkillFailure
from ..run import observe
from ..skill_plans import plan_pick
from ..sticky import SHUT
from ..sticky import note_grasp
from ..skills import (APPROACH_STEP, GRIP_CLOSED_BY, PICK_LEAVE_CHECK, PICK_REACH_TOL, PINCH_KINDS, _at_park, _carry_goal_set, _grasp_approach, _grasp_of, _pick_judged, _pinch_candidates, _surface_under, _travel_q, _turn, _watching, check_held, edge_held)


PICK_CAND_COST = 0.05          # m of park cost per rank of a grasp candidate (their order: centre, nearest first)


def _pick_problem(rig, name, cands, near, prefer=(), state=None):
    """The park of the pick of ``name``: every grasp candidate is one goal (its reach-in's start,
    the grasp, the first of the lift as the points the arm must reach; the reach-in's start as the
    relay pose the ranking solves), and a park counts when the whole pick plans from it
    (skill_plans.plan_pick, from the posture the arm arrives in, the hand opened to the
    candidate's width).  ``near`` / ``prefer`` as Problem's (the fridge shelf's open side, the pose a
    microwave was loaded from).  (Problem, the carry goal set)."""
    kin = rig.kin
    carry_goals = _carry_goal_set(rig, name)
    goals = []
    for i, g in enumerate(cands):
        u, L = _grasp_approach(g)
        start = np.asarray(g["p"], float) - L * np.asarray(u, float) / np.linalg.norm(u)
        goals.append(((start, np.asarray(g["p"], float), np.asarray(g["p"], float) + [0, 0, PICK_LEAVE_CHECK]),
                      (start, np.asarray(g["R"], float)), PICK_CAND_COST * i))

    def build(s, k, q_rank):
        g = cands[k]
        return plan_pick(kin, with_width(s, kin.side, g["pre_open"]), _grasp_of(name, g), *_grasp_approach(g),
                         carry_goals, q_seed=q_rank, step=APPROACH_STEP)

    travel = _travel_q(rig)
    arrive = lambda x, y, yaw: rig.q_cmd.copy() if _at_park(rig, x, y, yaw) else travel
    problem = Problem(tuple(goals), build, arrive, travel, near=near, prefer=tuple(prefer), label=f"pick {name}")
    return problem, carry_goals


def _pick_ready(rig, name, g, plan, carry_goals, out):
    """The pick's plan to run from the park, its builder for the rest, its hooks (run.run).  A grasp
    re-read off the one planned for (HINT_REACH / HINT_TURN) has the plan made again from here
    first.  Between the segments the pick's own steps: the object watched on the way in, the reach
    checked, the pinch judged and the load registered as held (``out["tcp0"]``: the TCP where the
    hand closed), the carry checked."""
    kin = rig.kin
    grasp = _grasp_of(name, g)
    u, L = _grasp_approach(g)
    planned = next((sg for sg in plan.segments if sg.name == "pick_grasp"), None) if plan is not None else None
    if planned is None or np.linalg.norm(planned.target[1] - grasp["p"]) > HINT_REACH or \
            _turn(planned.target[2], grasp["R"]) > HINT_TURN:
        rig.log("pick_plan_again", obj=name, why="no plan" if planned is None else "the grasp moved")
        plan = plan_pick(kin, observe(rig), grasp, u, L, carry_goals, step=APPROACH_STEP)
        if isinstance(plan, Failure):
            raise SkillFailure(f"pick {name}: {plan.segment}: {plan.why}")
    reach = next((sg for sg in plan.segments if sg.name == "pick_reach" and sg.qs), None)
    seed = None if reach is None else reach.q_end      # the plan's solution of the reach-in's start

    def rebuild(state, frm):
        return plan_pick(kin, state, grasp, u, L, carry_goals, start=frm, q_seed=seed, step=APPROACH_STEP)

    def after_grasp(rig):
        err = float(np.linalg.norm(kin.tcp(rig.q())[0] - grasp["p"]))
        if kin.motion is not None:
            # what the open hand at the commanded grasp pose penetrates in the full model (grasp_contacts)
            rig.log("grasp_contacts", obj=name, kind=g["kind"], tcp_err_m=round(err, 4),
                    hits=kin.motion.contacts_by_owner(kin, rig.q_cmd, kin._other_q()))
        if err > PICK_REACH_TOL:
            # stopped short of the grasp pose: something is in the way, closing here pinches elsewhere
            rig.log("pick_result", obj=name, kind=g["kind"], tcp_err_m=round(err, 4), held=False, why="blocked")
            rig.leave([0, 0, 1], "pick_fail_clear", LEAVE_CONTACT, step=0.005)
            rig.focus_z = None
            raise SkillFailure(f"pick {name}: the open hand stopped {err:.3f} m short of the grasp pose")

    def before_close(rig):
        rig.caption = f"PICK {name}: close gripper"
        if kin.motion is not None and kin.motion.by_owner.get(f"object:{name}"):
            out["T_obj0"], out["q_grasp"] = kin.motion.object_frames()[name], rig.q_cmd.copy()

    def after_close(rig):
        f = rig.fingers()
        if not np.all((f[:2] > SHUT) & (f[:2] < float(g["pre_open"]) - GRIP_CLOSED_BY)):
            # not pinched: shut on nothing, or a finger left where it opened (it met nothing).  Leave
            # with an open hand clear of the neighbours; nothing is held, so nothing is welded
            rig.log("pick_result", obj=name, kind=g["kind"], fingers=f.round(4).tolist(), held=False,
                    why="not pinched")
            rig.grip(0.04, 60)
            rig.leave([0, 0, 1], "pick_fail_clear", LEAVE_CONTACT, step=0.005)
            rig.focus_z = None
            raise SkillFailure(f"pick {name}: not held (fingers {np.round(f[:2], 4).tolist()}, "
                               f"opened to {g['pre_open']:.3f})")
        # held from here (and welded, under sticky hands): the hand's pose as it stands
        tcp0, R = kin.tcp(rig.q())
        rig.held = {"name": name, "kind": "pinch", "tcp_minus_body": tcp0 - rig.obj_pose(name)[0], "R": R,
                    "pre_open": g["pre_open"]}
        if g["kind"] == "thickness_pinch":
            # a flat object held at a side: what placing it flat needs (kind "edge", place_flat)
            rig.held.update(edge_held(rig, name, tcp0, R))
        out["tcp0"] = tcp0
        if "T_obj0" in out:
            # the hold a plan assumes (the load where it stood, the hand where it closed) against the
            # hold measured now: what skill_plans.HELD_POSE_MARGIN stands for
            rig.sync_world()
            p_g, R_g = kin.tcp(out["q_grasp"])
            T_g = np.eye(4)
            T_g[:3, :3], T_g[:3, 3] = R_g, p_g
            planned = np.linalg.inv(T_g) @ out["T_obj0"]
            measured = kin.motion.held_in_tcp(kin, rig.q_cmd, name)
            rig.log("held_offset", obj=name, kind=g["kind"],
                    offset_m=round(float(np.linalg.norm(measured[:3, 3] - planned[:3, 3])), 4),
                    turn_deg=round(math.degrees(_turn(planned[:3, :3], measured[:3, :3])), 2))
        rig.caption = f"PICK {name}: lift"

    watch = lambda: _watching(rig, name)
    hooks = {"pick_reach": {"around": watch}, "pick_grasp": {"around": watch, "after": after_grasp},
             "pick_close": {"before": before_close, "after": after_close},
             "carry_in": {"after": lambda rig: check_held(rig, "carry_in")}}
    return plan, rebuild, hooks


def pick_job(rig, args, state):
    """motion_skills.Job of the pinch pick: every grasp candidate one goal of the park search (the
    whole pick planned there, skill_plans.plan_pick); after the drive the candidate re-read, the plan
    run with the pick's hooks; then judged (_pick_judged)."""
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
    rig.sync_world()
    rig.focus_z = float(pos[2])
    bx, by, _ = rig.base_pose()
    # A fridge shelf is recessed behind its door. The robot's post-opening
    # pose biases the generic park search toward the hinge; seed the open
    # side of this shelf so a reachable rim grasp is considered promptly.
    fridge_shelf = str(obj.get("support", "")).startswith("breakfast_fridge/")
    microwave = next((a for a in rig.ann.articulated
                      if a["name"] == "kitchen_microwave" and "cavity_aabb" in a), None)
    cavity = microwave["cavity_aabb"] if microwave is not None else None
    in_microwave = microwave is not None and all(
        cavity[i] < pos[i] < cavity[i + 3] for i in range(3))
    retrieval_q = None
    if in_microwave:
        if abs(rig.joint("kitchen_microwave") - microwave["open_q"]) > 0.10:
            raise SkillFailure(f"pick {name}: microwave door is closed")
        # The only entry is from the front (low Y). Return to the arm/base
        # pose that physically cleared the open door during loading.
        retrieval_q = getattr(rig, "microwave_retrieval_q", None)
        search_near = (4.8, 1.7, 150.0) if retrieval_q is not None else (4.8, 1.7)
        cands.sort(key=lambda g: (g["p"][1], -g.get("tilt", 0),
                                  abs(g["p"][0] - (cavity[0] + cavity[3]) / 2)))
    elif fridge_shelf:
        search_near = (6.246, 2.337, 135.0)
        cands.sort(key=lambda g: (abs((g.get("azimuth", 0) + 180) % 360 - 180),
                                  -g.get("tilt", 0)))
    else:
        search_near = rig.base_pose()
        # off-centre pinch points of a long object let it swing in the hand:
        # prefer the centre, use the others when it is out of reach
        cands.sort(key=lambda g: np.linalg.norm(g["p"][:2] - np.array([bx, by])) + 0.3 * g.get("along_rank", 0))
    # every grasp candidate is one goal of the park search (park_search.find_park), and a park is
    # one where the whole pick can be planned (skill_plans.plan_pick) -- that plan is run.  In the
    # microwave too since 11-08: its candidates sorted by the cavity's opening (above), the pose it
    # was loaded from tried first; the old reach-in-only search, the relocation to the retrieval
    # posture and the written withdrawal points are retired (commented out below, step 6.4)
    near = rig.base_pose()
    prefer = ()
    if in_microwave:
        near = rig.base_pose()[:2] if len(search_near) == 3 else search_near
        prefer = (search_near,) if len(search_near) == 3 else ()
    elif fridge_shelf:
        near, prefer = rig.base_pose()[:2], (search_near,)
    goal_cands = cands[:max_candidates] + extra
    problem, carry_goals = _pick_problem(rig, name, goal_cands, near, prefer, state)
    ctx = {"out": {}}

    def no_park(diag):
        getattr(rig, "log", lambda *a, **k: None)("pick_no_park", obj=name, pos=[round(float(v), 3) for v in pos],
                quat=[round(float(v), 3) for v in quat], n_cands=len(cands), diag=diag)
        return SkillFailure(f"pick {name}: no reachable grasp from any base pose")

    def found_park(found):
        g = goal_cands[found.k]
        rig.log("pick_park", obj=name, kind=g["kind"], park=[round(found.x, 3), round(found.y, 3), round(found.yaw, 1)],
                floor=bool(floor_z < 0.05))
        rig.caption = f"PICK {name}: approach" + (" (torso down: floor)" if floor_z < 0.05 else "")

    def ready(found):
        g = goal_cands[found.k]
        # re-read after driving (the drive may have knocked it): the same candidate at the object's
        # pose now -- found by its place in the candidate list, not by an equal pose (a 1e-3 rotation
        # tolerance dropped every re-read of an object turned by a tenth of a degree)
        p_now, q_now = rig.obj_pose(name)
        now_c, now_x = _pinch_candidates(rig, obj, p_now, q_now, kinds, _surface_under(rig, name, rig.state()))
        g = next((c for c in now_c + now_x if c["idx"] == g["idx"]), g)
        rig.log("pick_target", obj=name, pos=[round(float(v), 3) for v in p_now],
                quat=[round(float(v), 3) for v in q_now], p=[round(float(v), 3) for v in g["p"]],
                kind=g["kind"], azimuth=g.get("azimuth"), tilt=g.get("tilt"))
        note_grasp(rig, name, g["p"], g["R"], "edge" if g["kind"] == "thickness_pinch" else "pinch", g["pre_open"])
        ctx["g"], ctx["pos"] = g, p_now
        return _pick_ready(rig, name, g, found.plan, carry_goals, ctx["out"])

    def failed(exc):
        if isinstance(exc, Dropped):
            return SkillFailure(f"pick {name}: not held ({exc})")
        return None

    def done():
        return _pick_judged(rig, name, ctx["g"], ctx["out"]["tcp0"], ctx["pos"])
    return Job(problem=problem, no_park=no_park, found=found_park, ready=ready, failed=failed, done=done)
