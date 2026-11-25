"""The drop's job (motion_skills.Job): a held load let go over a container's opening (docs/skills/drop_hover.md)."""

from __future__ import annotations

import math

import numpy as np

from ..annotations import rz
from ..park_search import Problem
from ..physics import CONTAINER_BASE_T, CONTAINER_WALL
from ..rig import SkillFailure
from ..run import observe
from ..skill_plans import DROP_RELAY, T_of
from ..skills import PLACE_SPOT_COST, PLACE_YAW_COST, PLACE_YAWS, _lowest_z, check_held
from ..tolerances import LEAVE_GAP, LEAVE_MARGIN
from .carry import _carry_bottom_z, carry_posture

OVER_OPENING = 0.6      # of the opening's radius: a load centred this close over it...
OVER_RIM_MAX = 0.25     # m: ...its lowest point above the rim and at most this far is let go where it is (a hover
#                         before; both inherited from the old drop_into)
FAR_M = 1.0             # m: a container this far from the base ranks parks by reach to it, not by distance from here
#                         (place_job's)


def drop_job(rig, args, state, skill=None):
    """motion_skills.Job of the drop into ``args["container"]`` (any container but a tray: place sets
    things down on a tray's floor): the carry posture settled above the rim first (carry_posture);
    the load over the opening -- its lowest point LEAVE_GAP above the rim, at the opening's centre and,
    where the load still clears the walls, off it toward each side -- with the hand turned about the
    vertical in PLACE_YAWS steps, each one goal of the park search (the whole drop planned there,
    skill_plans.plan_drop: reach, let go, fall, tuck); a load already held over the opening (a hover
    before) is let go where it is: its one goal the hold as it hangs, the base as it stands tried
    first.  After the drive the plan run with the drop's hooks; then the load judged inside."""
    from ..motion_skills import Job
    name, container = args["name"], args["container"]
    side = rig.hand_of(args["name"]) or "right"      # the hand that holds it (HAND_PLAN 9c)
    kin = rig.arm_kin(side)
    plan_drop = skill.build if skill is not None else _plan_drop()
    if rig.held_by(side) is None or rig.held_by(side)["name"] != name:
        raise SkillFailure(f"drop {name}: not holding it")
    ca = rig.ann.asset_of(rig.ann.objects[container]).get("container")
    if not ca:
        raise SkillFailure(f"drop {name}: {container} is not a container")
    st = rig.state()
    cb = np.asarray(rig.geo.bottom(container, st), float)
    rim_z = float(cb[2] + ca["rim_height"])
    floor_z = float(cb[2]) + CONTAINER_BASE_T
    size = rig.ann.asset_of(rig.ann.objects[container])["size"]
    inner = float(ca.get("rim_radius") or 0.0) or 0.5 * float(min(size[:2]))
    fp = rig.geo.footprint(name, st)
    centre = np.array([(fp[0] + fp[2]) / 2, (fp[1] + fp[3]) / 2])
    low = float(_lowest_z(rig, name, st))
    here = bool(np.linalg.norm(centre - cb[:2]) < OVER_OPENING * inner and rim_z < low < rim_z + OVER_RIM_MAX)
    travel = {}
    if here:
        rig.log("drop_in_place", obj=name, container=container, height_above_rim=round(low - rim_z, 3))
        tcp, R = kin.tcp(rig.chain_q(side))
        poses, cost, fall = [(np.asarray(tcp, float), np.asarray(R, float), 0, 0)], [0.0], low - floor_z
    else:
        carry_bottom_z = _carry_bottom_z(rig, container)
        carry_posture(rig, min_bottom_z=carry_bottom_z, label="drop_carry", side=side)
        check_held(rig, "drop_carry", open_hand=False, side=side)
        rig.sync_world()
        travel = {"min_bottom_z": carry_bottom_z, "raise_load": False}
        st = rig.state()
        # the TCP measured (rig.q()), as the State's hold is (place_job: the arm's sag under the load
        # read against the command is a shifted hold)
        tcp, R = kin.tcp(rig.chain_q(side))
        body = np.asarray(rig.obj_pose(name)[0], float)
        hang = float(body[2] - _lowest_z(rig, name, st))
        osz = rig.ann.asset_of(rig.ann.objects[name])["size"]
        room = inner - 0.5 * math.hypot(osz[0], osz[1]) - CONTAINER_WALL - LEAVE_GAP
        z = rim_z + LEAVE_GAP + hang
        # the opening's centre, and off it toward each side as far as the load still clears the walls:
        # a bin deep on a table is out of reach at its centre
        anchors = [np.r_[cb[:2], z]] + ([np.r_[cb[:2] + room * np.asarray(d, float), z]
                                         for d in ((1, 0), (-1, 0), (0, 1), (0, -1))] if room > LEAVE_MARGIN else [])
        off = np.asarray(tcp, float) - body
        poses, cost = [], []
        for i, a in enumerate(anchors):
            for deg in PLACE_YAWS:
                Rz = rz(math.radians(deg))
                poses.append((a + Rz @ off, Rz @ np.asarray(R, float), deg, i))
                cost.append(PLACE_YAW_COST * abs(deg) / 45.0 + (PLACE_SPOT_COST if i else 0.0))
        fall = rim_z + LEAVE_GAP - floor_z
    # what plan_drop takes: the pose of the load's box frame each goal puts it at, through the hold the
    # State has now (the plan derives the TCP back from the hold it is built with, as plan_place)
    held = observe(rig).held(kin.side)
    T_hold = np.eye(4) if held is None else np.asarray(held.T_tcp_obj, float)
    targets = [T_of(Rg, p) @ T_hold for p, Rg, _, _ in poses]
    open_w = float(rig.held_by(side).get("pre_open", 0.04))
    rests = (kin.rest, kin.drive)
    near = rig.base_pose()
    if not here and math.hypot(near[0] - cb[0], near[1] - cb[1]) > FAR_M:
        near = None

    def build(st_, k, prior):
        return plan_drop(kin, st_, targets[k], open_w, rests, container, fall, prior=prior, obj=name)
    problem = Problem(tuple(((p,), (p, Rg), c) for (p, Rg, _, _), c in zip(poses, cost)), build, DROP_RELAY,
                      near=None if near is None else tuple(near), label=f"drop {name}", hand=side)

    def no_park(diag):
        return SkillFailure(f"drop {name}: no base pose above {container} "
                            f"({len(poses)} goals; rejected: { {k: v for k, v in diag.items() if v} })")

    def found_park(found):
        _, _, deg, i = poses[found.k]
        rig.log("drop_park", obj=name, park=[round(found.x, 3), round(found.y, 3), round(found.yaw, 1)],
                yaw_deg=deg, anchor=i, goals=len(poses))
        rig.caption = f"DROP {name} into {container}"

    def ready(found):
        k = found.k

        def rebuild(state_, frm, prior):
            return plan_drop(kin, state_, targets[k], open_w, rests, container, fall, start=frm, prior=prior, obj=name)

        def after_reach(r):
            check_held(r, "drop_above", open_hand=False, side=side)

        def after_release(r):
            r.set_held(side, None)
        return found.plan, rebuild, {"drop_reach": {"after": after_reach}, "drop_release": {"after": after_release}}

    def done():
        ok, why = rig.geo.inside(name, container, rig.state())
        rig.log("drop_result", obj=name, container=container, inside=bool(ok), detail=why)
        if not ok:
            raise SkillFailure(f"drop {name} into {container}: {why}")
        return True
    return Job(problem=problem, no_park=no_park, found=found_park, travel=travel, ready=ready, done=done)


def _plan_drop():
    from ..skill_plans import plan_drop
    return plan_drop


HOVER_CLEAR = 0.06      # m: a hover holds the load's lowest point this far above the target's top (the old
#                         HoverOverPolicy's clearance_m; hovering_over asks 0.03-0.15 m, centred within 4 cm)


def hover_job(rig, args, state, skill=None):
    """motion_skills.Job of hover (HAND_PLAN 9e; docs/skills/drop_hover.md): what a hand holds
    (``args["name"]``) held with its lowest point HOVER_CLEAR above the top of ``args["target"]`` (an object:
    its bottom plus its rim height, or its height; else its annotated point), centred over it, the hand turned
    about the vertical in PLACE_YAWS steps -- each one goal of the park search, the plan the drop's without
    the release (skill_plans.plan_hover).  The carry posture settled above that height first (carry_posture,
    a wish: the old stow_load).  done(): the load's bottom above the target's top, returned with how far."""
    from ..motion_skills import Job
    from ..predicates import entity_kind, entity_point
    from ..skill_plans import HOVER_RELAY, plan_hover as _default
    plan_hover = skill.build if skill is not None else _default
    name, target = args["name"], args["target"]
    side = rig.hand_of(name)
    if side is None:
        raise SkillFailure(f"hover {name}: not held")
    kin = rig.arm_kin(side)
    st = rig.state()
    kind, rec = entity_kind(rig.ann, target)
    if kind == "object":
        t = np.asarray(rig.geo.bottom(target, st), float)
        a = rig.ann.asset_of(rec)
        top, c = float(t[2] + (a["container"]["rim_height"] if a.get("container") else a["size"][2])), t[:2]
    else:
        p = np.asarray(entity_point(rig, target, st), float)
        top, c = float(p[2]), p[:2]
    carry_posture(rig, min_bottom_z=top + HOVER_CLEAR, label="hover_carry", side=side)
    check_held(rig, "hover_carry", open_hand=False, side=side)
    rig.sync_world()
    st = rig.state()
    # the TCP measured (rig.q()), as the State's hold is (drop_job)
    tcp, R = kin.tcp(rig.chain_q(side))
    body = np.asarray(rig.obj_pose(name)[0], float)
    hang = float(body[2] - _lowest_z(rig, name, st))
    b = np.asarray(rig.geo.bottom(name, st), float)
    off = np.asarray(tcp, float) - np.r_[b[:2], body[2]]   # TCP minus the load's bottom centre at its body height
    at = np.r_[c, top + HOVER_CLEAR + hang]
    poses, cost = [], []
    for deg in PLACE_YAWS:
        Rz = rz(math.radians(deg))
        poses.append((at + Rz @ off, Rz @ np.asarray(R, float), deg))
        cost.append(PLACE_YAW_COST * abs(deg) / 45.0)
    held = observe(rig).held(kin.side)
    T_hold = np.eye(4) if held is None else np.asarray(held.T_tcp_obj, float)
    targets = [T_of(Rg, p) @ T_hold for p, Rg, _ in poses]
    near = rig.base_pose()
    if math.hypot(near[0] - c[0], near[1] - c[1]) > FAR_M:
        near = None

    def build(st_, k, prior):
        return plan_hover(kin, st_, targets[k], prior=prior, obj=name)
    problem = Problem(tuple(((p,), (p, Rg), cs) for (p, Rg, _), cs in zip(poses, cost)), build, HOVER_RELAY,
                      near=None if near is None else tuple(near), label=f"hover {name}", hand=side)

    def no_park(diag):
        return SkillFailure(f"hover {name}: no base pose above {target} "
                            f"({len(poses)} goals; rejected: { {k: v for k, v in diag.items() if v} })")

    def found_park(found):
        rig.log("hover_park", obj=name, target=target, park=[round(found.x, 3), round(found.y, 3), round(found.yaw, 1)],
                yaw_deg=poses[found.k][2], goals=len(poses))
        rig.caption = f"HOVER {name} over {target}"

    def ready(found):
        k = found.k

        def rebuild(state_, frm, prior):
            return plan_hover(kin, state_, targets[k], start=frm, prior=prior, obj=name)
        return found.plan, rebuild, {"hover_reach": {"after": lambda r: check_held(r, "hover", open_hand=False,
                                                                                  side=side)}}

    def done():
        above = float(rig.geo.bottom(name, rig.state())[2] - top)
        rig.log("hover_result", obj=name, target=target, hand=side, bottom_above_target_m=round(above, 3))
        if above <= 0.0:
            raise SkillFailure(f"hover {name}: its bottom {above:.3f} m above {target}'s top")
        return {"bottom_above_target_m": above, "hang_m": hang}
    return Job(problem=problem, no_park=no_park, found=found_park,
               travel={"min_bottom_z": top + HOVER_CLEAR, "raise_load": False}, ready=ready, done=done)
