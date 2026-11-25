"""The pour's job (motion_skills.Job, the catalog's "pour"; HAND_PLAN 9h): a held cup tilted over a container until its
contents fall out -- every way to hold it over the opening one goal of the park search, the whole pour planned there
(skill_plans.plan_pour); judged by where the contents went."""

from __future__ import annotations

import math

import numpy as np
from scipy.spatial.transform import Rotation

from ..park_search import VARIANT_COST, Problem
from ..predicates import objects_inside
from ..rig import SkillFailure
from ..skill_plans import POUR_RELAY
from ..skills import check_held
from .carry import carry_posture

POUR_TILT = math.radians(110.0)      # rad: the tilt goes this far at most (the old largest commanded tilt)
POUR_MIN_TILT = math.radians(60.0)   # rad: a park whose arm tilts it less is rejected in the build (the old rocking
#                                      threshold: below it nothing poured)
POUR_YAWS = (0.0, 45.0, -45.0, 90.0, -90.0, 180.0)   # deg the hand (and the pour) turns about the vertical
POUR_ABOVE = 0.05                    # m: the cup's bottom this far over the target's rim at the start (old value)


def pour_job(rig, args, state, skill=None):
    """motion_skills.Job of pouring ``args["source"]`` (a held cup with items in it, either hand) into ``args["target"]``
    (a container): the load first in the carry posture above the rim (carry_posture); the cup's lip over the opening's
    centre or a little toward the robot, POUR_ABOVE over the rim, the hand turned about the vertical in POUR_YAWS -- a
    rim-held cup pours away from the hand (the tilt about the horizontal across that), a handle-held one also sideways
    either way -- each one goal of the park search; the tilt about the point half-way from the hand to the lip
    (plan_pour), a park whose arm tilts it less than POUR_MIN_TILT rejected.  done(): at least half the items inside
    the target (SkillFailure otherwise), those returned."""
    from ..motion_skills import Job
    from ..run import observe
    source, target = args["source"], args["target"]
    side = rig.hand_of(source)
    if side is None:
        raise SkillFailure(f"pour: {source} is not held")
    st = rig.state()
    items = objects_inside(rig, source, st)
    if not items:
        raise SkillFailure(f"pour: {source} holds no items")
    ta = rig.ann.asset_of(rig.ann.objects[target]).get("container")
    if not ta:
        raise SkillFailure(f"pour: {target} is not a container")
    tb = np.asarray(rig.geo.bottom(target, st), float)
    rim_z = float(tb[2] + ta["rim_height"])
    carry_posture(rig, min_bottom_z=rim_z + POUR_ABOVE, label="pour_carry", side=side)
    check_held(rig, "pour_carry", open_hand=False, side=side)
    rig.sync_world()
    st = rig.state()
    kin = rig.arm_kin(side)
    tcp, R = kin.tcp(rig.chain_q(side))
    tcp, R = np.asarray(tcp, float), np.asarray(R, float)
    held = rig.held_by(side)
    sa = rig.ann.asset_of(rig.ann.objects[source])
    c_cup = np.asarray(rig.geo.centre(source, st), float)
    o_in = c_cup[:2] - tcp[:2]                       # TCP -> cup centre (horizontal)
    u_in = o_in / np.linalg.norm(o_in) if np.linalg.norm(o_in) > 1e-3 else np.array([1.0, 0.0])
    handle = held.get("grasp") == "handle"
    cup_r = 0.5 * float(max(sa["size"][:2]))
    if handle:
        cup_r = float((sa.get("container") or {}).get("rim_radius", cup_r))
    src_rim = float((sa.get("container") or {}).get("rim_height", sa["size"][2]))
    bottom_now = float(rig.geo.bottom(source, st)[2])
    lip_dz = src_rim - float(tcp[2] - bottom_now)    # the lip's height above the TCP
    lift = rim_z + POUR_ABOVE - bottom_now           # how far the TCP goes up for the cup's bottom to clear the rim
    side_in = np.array([-u_in[1], u_in[0]])
    # (the pour's direction in the hand's frame, the lip off the TCP): away from the hand; a handle pinch sideways
    variants = [(side_in, o_in + side_in * cup_r), (-side_in, o_in - side_in * cup_r)] if handle else \
        [(u_in, u_in * 2 * cup_r)]
    t_rim = 0.5 * float(min(rig.ann.asset_of(rig.ann.objects[target])["size"][:2]))
    bxy = np.asarray(rig.base_pose()[:2], float)
    to_base = (bxy - tb[:2]) / max(1e-9, float(np.linalg.norm(bxy - tb[:2])))
    pours, goals = [], []
    for j, psi in enumerate(POUR_YAWS):
        Rz = Rotation.from_euler("z", math.radians(psi)).as_matrix()
        for lip_off in (0.0, min(0.05, 0.5 * t_rim)):
            for u_b, lip_b in variants:
                u = (Rz @ np.r_[u_b, 0.0])[:2]
                lip = (Rz @ np.r_[lip_b, 0.0])[:2]
                p = np.r_[tb[:2] + to_base * lip_off - lip, tcp[2] + lift]
                Rg = Rz @ R
                pivot = p + 0.5 * np.r_[lip, lip_dz]
                axis = np.cross([0.0, 0.0, 1.0], np.r_[u, 0.0])
                axis /= np.linalg.norm(axis)
                pours.append({"source": source, "target": target, "p": p, "R": Rg, "pivot": pivot, "axis": axis,
                              "tilt": POUR_TILT, "yaw": psi, "lip_off": lip_off})
                goals.append(((p,), (p, Rg), VARIANT_COST * j + (0.5 * VARIANT_COST if lip_off else 0.0)))
    build_with = skill.build if skill is not None else None
    if build_with is None:
        from ..skill_plans import plan_pour as build_with

    def build(s, k, prior):
        plan = build_with(kin, s, pours[k], prior=prior)
        tilt = getattr(plan, "info", {}).get("tilt_rad") if not hasattr(plan, "why") else None
        if tilt is not None and tilt < POUR_MIN_TILT:
            from ..motion_state import Failure
            return Failure(f"the arm tilts it only {math.degrees(tilt):.0f} deg", "pour_tilt")
        return plan
    problem = Problem(tuple(goals), build, POUR_RELAY, near=rig.base_pose(), label=f"pour {source}", hand=side)
    ctx = {}

    def no_park(diag):
        return SkillFailure(f"pour: no base pose holds {source} over {target} "
                            f"({len(goals)} goals; rejected: { {k: v for k, v in diag.items() if v} })")

    def found_park(found):
        pr = pours[found.k]
        ctx["tilt"] = found.plan.info.get("tilt_rad")
        rig.log("pour_plan", source=source, target=target, hand=side, yaw_deg=pr["yaw"], lip_offset_m=pr["lip_off"],
                tilt_deg=round(math.degrees(ctx["tilt"] or 0.0), 1),
                park=[round(found.x, 3), round(found.y, 3), round(found.yaw, 1)])
        rig.caption = f"POUR {source} into {target}"

    def ready(found):
        pr = pours[found.k]

        def rebuild(state_, frm, prior):
            return build_with(kin, state_, pr, start=frm, prior=prior)
        return found.plan, rebuild, {"pour_back": {"after": lambda r: check_held(r, "pour_return", open_hand=False,
                                                                                 side=side)}}

    def done():
        moved = [n for n in items if rig.geo.inside(n, target, rig.state())[0]]
        rig.log("pour_result", source=source, target=target, hand=side,
                tilt_deg=round(math.degrees(ctx.get("tilt") or 0.0), 1), moved=moved, items=items)
        if len(moved) < math.ceil(len(items) / 2):
            raise SkillFailure(f"pour: {len(moved)}/{len(items)} items reached {target}")
        return moved
    return Job(problem=problem, no_park=no_park, found=found_park, ready=ready, done=done)
