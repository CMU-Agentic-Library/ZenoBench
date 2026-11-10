"""The pinch pick's job (motion_skills.Job): the park search's problem, the plan to run after the drive, the result."""

from __future__ import annotations

import math
import numpy as np

from ..motion_state import Failure, clearing
from ..park_search import Problem
from ..rig import Dropped
from ..primitives import near_pose, turn
from ..rig import SkillFailure
from ..run import observe
from ..sticky import SHUT
from ..sticky import note_grasp
from ..skill_plans import PICK_RELAY
from ..skills import (APPROACH_STEP, GRIP_CLOSED_BY, PICK_LEAVE_CHECK, PICK_REACH_TOL, PINCH_KINDS, _carry_goal_set, _grasp_approach, _grasp_of, _pick_judged, _pinch_candidates, _surface_under, _watching, check_held, edge_held)


PICK_CAND_COST = 0.05          # m of park cost per rank of a grasp candidate (their order: centre, nearest first)


def _pick_problem(rig, name, cands, near, prefer=(), build_with=None):
    """The park of the pick of ``name``: every grasp candidate is one goal (its reach-in's start,
    the grasp, the first of the lift as the points the arm must reach; the reach-in's start as the
    relay pose the ranking solves), and a park counts when the whole pick plans from it
    (``build_with``: the catalog's builder, skill_plans.plan_pick, from the posture the arm arrives
    in -- run_skill sets it from the catalog -- the hand opened to the candidate's width).  ``near`` /
    ``prefer`` as Problem's (in front of a door's free edge: _front_of).  (Problem, the carry goal set)."""
    kin = rig.kin
    build_with = build_with or _plan_pick()
    carry_goals = _carry_goal_set(rig, name)
    goals = []
    for i, g in enumerate(cands):
        u, L = _grasp_approach(g)
        start = np.asarray(g["p"], float) - L * np.asarray(u, float) / np.linalg.norm(u)
        goals.append(((start, np.asarray(g["p"], float), np.asarray(g["p"], float) + [0, 0, PICK_LEAVE_CHECK]),
                      (start, np.asarray(g["R"], float)), PICK_CAND_COST * i))

    def build(s, k, prior):
        g = cands[k]
        return build_with(kin, s, _grasp_of(name, g), *_grasp_approach(g), carry_goals, prior=prior,
                          step=APPROACH_STEP)

    problem = Problem(tuple(goals), build, PICK_RELAY, near=near, prefer=tuple(prefer), label=f"pick {name}")
    return problem, carry_goals


FRONT_SEED_M = 0.65            # m in front of a door's free edge the first park of a pick behind it stands
                               # (the hand-placed fridge seed of 11-0x stood 0.67 m out, 6 cm past the edge)


def _outward(a):
    """The unit horizontal direction out of articulated ``a``'s opening: its handle's outward normal."""
    out = np.asarray(a["handle"]["outward"], float)[:2]
    return out / np.linalg.norm(out)


def _behind_door(rig, obj, pos):
    """The articulated (with a door handle) ``obj`` stands behind: in its cavity, or on one of its
    inside supports ("<name>/inside_...": a shelf, a drawer's bottom) -- not on its top."""
    sup = str(obj.get("support", ""))
    for a in rig.ann.articulated:
        if not isinstance(a.get("handle"), dict) or "outward" not in a["handle"]:
            continue
        cav = a.get("cavity_aabb")
        if cav is not None and all(cav[i] < pos[i] < cav[i + 3] for i in range(3)):
            return a
        if sup.startswith(a["name"] + "/inside"):
            return a
    return None


def _front_of(rig, a, target):
    """A base pose FRONT_SEED_M out of ``a``'s opening (_outward) in front of its door's free edge --
    the end of the closed door away from the hinge, where the open door is not; the handle for a
    drawer -- facing ``target`` with it off to the right arm's side by park_search.FACE_LEFT, as the
    candidates' cost prefers (and the hand-placed seeds had it)."""
    from ..park_search import FACE_LEFT
    out = _outward(a)
    if a.get("type") == "revolute":
        T = rig.ann.part_pose(a, a["closed_q"])
        boxes = a.get("part_boxes") or [a["part_box"]]
        ends = [T[:3, :3] @ np.array([x, 0.5 * (lo[1] + hi[1]), 0.0]) + T[:3, 3]
                for lo, hi in boxes for x in (lo[0], hi[0])]
        pivot = np.asarray(a["pivot"], float)
        edge = max(ends, key=lambda e: float(np.hypot(*(e - pivot)[:2])))[:2]
    else:
        edge = np.asarray(a["handle"]["center"], float)[:2]
    xy = edge + FRONT_SEED_M * out
    face = math.degrees(math.atan2(target[1] - xy[1], target[0] - xy[0]))
    return float(xy[0]), float(xy[1]), float(face + FACE_LEFT)


def _plan_pick():
    from ..skill_plans import plan_pick
    return plan_pick


def _pick_ready(rig, name, g, plan, carry_goals, out, plan_pick=None):
    """The pick's plan to run from the park, its builder for the rest, its hooks (run.run).  A grasp
    re-read off the one planned for (primitives.near_pose) has the plan made again from here
    first, its decisions kept as they still hold (the prior: decide_ik).  Between the segments the
    pick's own steps: the object watched on the way in, the reach checked, the pinch judged and the
    load registered as held (``out["tcp0"]``: the TCP where the hand closed), the carry checked."""
    kin = rig.kin
    plan_pick = plan_pick or _plan_pick()
    grasp = _grasp_of(name, g)
    u, L = _grasp_approach(g)
    planned = next((sg for sg in plan.segments if sg.name == "pick_grasp"), None) if plan is not None else None
    if planned is None or not near_pose(planned.target[1], planned.target[2], grasp["p"], grasp["R"]):
        rig.log("pick_plan_again", obj=name, why="no plan" if planned is None else "the grasp moved")
        plan = plan_pick(kin, observe(rig), grasp, u, L, carry_goals, prior=plan, step=APPROACH_STEP)
        if isinstance(plan, Failure):
            raise SkillFailure(f"pick {name}: {plan.segment}: {plan.why}")

    def rebuild(state, frm, prior):
        return plan_pick(kin, state, grasp, u, L, carry_goals, start=frm, prior=prior, step=APPROACH_STEP)

    def after_grasp(rig):
        err = float(np.linalg.norm(kin.tcp(rig.q())[0] - grasp["p"]))
        if kin.motion is not None:
            # what the open hand at the commanded grasp pose penetrates in the full model (grasp_contacts)
            rig.log("grasp_contacts", obj=name, kind=g["kind"], tcp_err_m=round(err, 4),
                    hits=kin.motion.contacts_by_owner(kin, rig.q_cmd, kin._other_q()))
        if err > PICK_REACH_TOL:
            # stopped short of the grasp pose: something is in the way, closing here pinches elsewhere
            rig.log("pick_result", obj=name, kind=g["kind"], tcp_err_m=round(err, 4), held=False, why="blocked")
            rig.focus_z = None
            # out of the contact straight up: the failure exit run makes (skill_plans.plan_clear)
            raise clearing(SkillFailure(f"pick {name}: the open hand stopped {err:.3f} m short of the grasp pose"))

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
            rig.focus_z = None
            # the hand opened and out of the contact: the failure exit run makes (plan_clear)
            raise clearing(SkillFailure(f"pick {name}: not held (fingers {np.round(f[:2], 4).tolist()}, "
                                        f"opened to {g['pre_open']:.3f})"), 0.04)
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
                    turn_deg=round(math.degrees(turn(planned[:3, :3], measured[:3, :3])), 2))
        rig.caption = f"PICK {name}: lift"

    watch = lambda: _watching(rig, name)
    hooks = {"pick_reach": {"around": watch}, "pick_grasp": {"around": watch, "after": after_grasp},
             "pick_close": {"before": before_close, "after": after_close},
             "carry_in": {"after": lambda rig: check_held(rig, "carry_in", open_hand=False)}}
    return plan, rebuild, hooks


def pick_job(rig, args, state, skill=None):
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
    # behind a door (a cavity it stands in, a shelf of the articulated): the robot's pose after
    # opening it biases the search toward the hinge, so a park in front of the door's free edge is
    # tried first (_front_of, from the annotation: no scene's coordinates written here), and the
    # grasps most outward (toward the opening) first
    door = _behind_door(rig, obj, pos)
    near, prefer = rig.base_pose(), ()
    if door is not None:
        if abs(rig.joint(door["name"]) - door["open_q"]) > 0.10:
            raise SkillFailure(f"pick {name}: {door['name']} door is closed")
        out = _outward(door)
        prefer, near = (_front_of(rig, door, pos),), rig.base_pose()[:2]
        across = np.array([-out[1], out[0]])
        cands.sort(key=lambda g: (-float(np.asarray(g["p"])[:2] @ out), -g.get("tilt", 0),
                                  abs(float((np.asarray(g["p"])[:2] - np.asarray(pos)[:2]) @ across))))
    else:
        # off-centre pinch points of a long object let it swing in the hand:
        # prefer the centre, use the others when it is out of reach
        cands.sort(key=lambda g: np.linalg.norm(g["p"][:2] - np.array([bx, by])) + 0.3 * g.get("along_rank", 0))
    # every grasp candidate is one goal of the park search (park_search.find_park), and a park is
    # one where the whole pick can be planned (skill_plans.plan_pick) -- that plan is run
    goal_cands = cands[:max_candidates] + extra
    build_with = skill.build if skill is not None else None
    problem, carry_goals = _pick_problem(rig, name, goal_cands, near, prefer, build_with)
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
        return _pick_ready(rig, name, g, found.plan, carry_goals, ctx["out"], build_with)

    def failed(exc):
        if isinstance(exc, Dropped):
            return SkillFailure(f"pick {name}: not held ({exc})")
        return None

    def done():
        return _pick_judged(rig, name, ctx["g"], ctx["out"]["tcp0"], ctx["pos"])
    return Job(problem=problem, no_park=no_park, found=found_park, ready=ready, failed=failed, done=done)
