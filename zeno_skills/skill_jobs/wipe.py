"""The wipe's job (motion_skills.Job, the catalog's "wipe"; HAND_PLAN 9g, docs/skills/wipe.md): a held sponge pressed
on a free strip along an edge of a support and stroked along it by the arm -- every strip and turn of the hand one
goal of the park search, the whole wipe planned there (skill_plans.plan_wipe); the coverage measured from the
sponge as the simulator has it while it strokes."""

from __future__ import annotations

import math

import numpy as np
from scipy.spatial.transform import Rotation

from ..park_search import Problem
from ..predicates import memory
from ..rig import SkillFailure
from ..skill_plans import WIPE_RELAY
from ..skills import _lowest_z, _overlaps_objects, check_held
from ..tolerances import LEAVE_GAP, LEAVE_MARGIN, WIPE_PRESS
from .carry import carry_posture

WIPE_LENGTH = 0.30            # m: the strip wiped (the old policy's)
WIPE_INSETS = (0.08, 0.045)   # m in from a support edge a wipe strip runs (the second when objects line the first)
WIPE_STEP_ALONG = 0.10        # m between strip centres sampled along an edge
WIPE_STRIPS = 8               # cheapest free strips in the park goal set (x WIPE_YAWS)
WIPE_DIST_COST = 0.3          # park cost per m from the robot to a strip's centre
WIPE_INSET_COST = 0.05        # park cost of the closer-to-the-edge inset
WIPE_YAWS = (0.0, 90.0, -90.0, 180.0)   # deg the hand (and the sponge) turns about the vertical: it does not matter
WIPE_COVER = 0.5              # of the strip's 2 cm cells under the sponge while pressed: the wiped predicate's
WIPE_CELL = 0.02              # m: a coverage cell
WIPE_ON = 0.008               # m: the sponge's lowest point this close to the surface counts as pressed (old value)
WIPE_EVERY = 4                # physics ticks between coverage samples


def _strips(rig, tool, s, length, width, base):
    """(cost, a, b) of the free strips of support ``s`` (the old WipeSurfacePolicy's sampling): along each edge,
    WIPE_INSETS in, every WIPE_STEP_ALONG, ``length`` long and ``width`` wide, none over another object; the
    WIPE_STRIPS cheapest (nearest ``base``)."""
    st = rig.state()
    x0, y0, x1, y1 = s["aabb_xy"]
    out = []
    for inward in (np.array([1.0, 0.0]), np.array([-1.0, 0.0]), np.array([0.0, 1.0]), np.array([0.0, -1.0])):
        along = np.array([-inward[1], inward[0]])
        k = 0 if inward[0] else 1
        lo, hi = ((y0, y1) if k == 0 else (x0, x1))
        for inset in WIPE_INSETS:
            line = (x0, y0)[k] + inset if inward[k] > 0 else (x1, y1)[k] - inset
            for t in np.arange(lo + 0.03 + length / 2, hi - 0.03 - length / 2 + 1e-6, WIPE_STEP_ALONG):
                c = np.array([line, t]) if k == 0 else np.array([t, line])
                a, b = c - along * length / 2, c + along * length / 2
                box_lo, box_hi = np.minimum(a, b) - width / 2, np.maximum(a, b) + width / 2
                if _overlaps_objects(rig, [box_lo[0], box_lo[1], box_hi[0], box_hi[1], s["z"], s["z"] + 0.2], {tool},
                                     st, margin=0.02):
                    continue
                cost = WIPE_DIST_COST * math.hypot(c[0] - base[0], c[1] - base[1]) + \
                    (WIPE_INSET_COST if inset != WIPE_INSETS[0] else 0.0)
                out.append((cost, a, b))
    return sorted(out, key=lambda t: t[0])[:WIPE_STRIPS]


def wipe_job(rig, args, state, skill=None):
    """motion_skills.Job of wiping ``args["support"]`` with ``args["tool"]`` (held in either hand): the load first in
    the carry posture (carry_posture, the old stow_load); every free strip (_strips) x hand turn (WIPE_YAWS) one goal
    of the park search -- the press's pose the TCP that puts the sponge's bottom centre WIPE_PRESS into the surface
    at the strip's start through the hold the State has, the stroke along it (plan_wipe) -- a stroke too short for
    WIPE_COVER of the strip a Failure of plan_wipe itself ("need"), at a park and in a rebuild alike.  After the drive the plan run with the wipe's
    hooks: the sponge sampled every WIPE_EVERY ticks while it strokes, a WIPE_CELL cell of the strip covered while
    its lowest point is within WIPE_ON of the surface (the old rule, now on every tick).  Judged: at least
    WIPE_COVER covered (memory "wiped")."""
    from ..motion_skills import Job
    from ..run import observe
    tool, support = args["tool"], args["support"]
    length = float(args.get("length", WIPE_LENGTH))
    side = rig.hand_of(tool)
    if side is None:
        raise SkillFailure(f"wipe: {tool} is not held")
    s = rig.ann.support(support)
    furniture = s.get("furniture") or support.split("/")[0]
    size = np.asarray(rig.ann.asset_of(rig.ann.objects[tool])["size"], float)
    width, half = float(min(size[:2])), 0.5 * float(max(size[:2]))
    strips = _strips(rig, tool, s, length, width, rig.base_pose())
    if not strips:
        raise SkillFailure(f"wipe {support}: no free strip")
    carry_posture(rig, label="wipe_carry", side=side)
    check_held(rig, "wipe_carry", open_hand=False, side=side)
    rig.sync_world()
    kin = rig.arm_kin(side)
    st = rig.state()
    body = np.asarray(rig.obj_pose(tool)[0], float)
    hang = float(body[2] - _lowest_z(rig, tool, st))
    held = observe(rig).held(side)
    T_hold = np.asarray(held.T_tcp_obj, float)       # the sponge's box frame in the TCP frame
    _, R_now = kin.tcp(rig.chain_q(side))
    above = WIPE_PRESS + LEAVE_GAP + LEAVE_MARGIN
    need = max(0.0, WIPE_COVER * length - half)      # m the stroke must run for WIPE_COVER of the strip
    wipes, goals = [], []
    for c_strip, a, b in strips:
        for psi in WIPE_YAWS:
            Rk = Rotation.from_euler("z", math.radians(psi)).as_matrix() @ np.asarray(R_now, float)
            # the TCP that puts the sponge's body origin over a, its bottom WIPE_PRESS into the surface
            body_at = np.r_[a, s["z"] - WIPE_PRESS + hang]
            p = body_at - Rk @ T_hold[:3, 3]
            d = np.r_[b - a, 0.0]
            wipes.append({"support": furniture, "p": p, "R": Rk, "d": d, "above": above, "need": need, "strip": (a, b),
                          "yaw": psi})
            goals.append(((p + [0.0, 0.0, above], p, p + d), (p, Rk), c_strip))
    build_with = skill.build if skill is not None else None
    if build_with is None:
        from ..skill_plans import plan_wipe as build_with

    def build(st_, k, prior):
        return build_with(kin, st_, wipes[k], prior=prior)
    problem = Problem(tuple(goals), build, WIPE_RELAY, near=rig.base_pose(), label=f"wipe {support}", hand=side)
    ctx = {"n": 0}

    def no_park(diag):
        return SkillFailure(f"wipe {support}: no base pose reaches any of {len(strips)} free strips "
                            f"({len(goals)} goals; rejected: { {k: v for k, v in diag.items() if v} })")

    def found_park(found):
        w = wipes[found.k]
        ctx["w"] = w
        ctx["covered"] = np.zeros(max(1, int(round(length / WIPE_CELL))), bool)
        rig.log("wipe_plan", strip=[np.round(v, 3).tolist() for v in w["strip"]], yaw_deg=w["yaw"], hand=side,
                stroke_m=round(float(found.plan.info.get("stroke_m") or 0.0), 3), strips=len(strips), goals=len(goals),
                park=[round(found.x, 3), round(found.y, 3), round(found.yaw, 1)])
        rig.caption = f"WIPE {support} with {tool}"

    def sample():
        ctx["n"] += 1
        if ctx["n"] % WIPE_EVERY:
            return
        st2 = rig.state()
        if abs(float(_lowest_z(rig, tool, st2)) - s["z"]) > WIPE_ON:
            return
        a, b = ctx["w"]["strip"]
        cov = ctx["covered"]
        u = float((np.asarray(rig.geo.bottom(tool, st2), float)[:2] - a) @ (b - a) / (length ** 2))
        h = half / length
        i0, i1 = int(max(0, (u - h) * len(cov))), int(min(len(cov), math.ceil((u + h) * len(cov))))
        cov[i0:i1] = True

    class _Sampling:
        def __enter__(self):
            rig.tick_watchers.append(sample)

        def __exit__(self, *exc):
            if sample in rig.tick_watchers:
                rig.tick_watchers.remove(sample)
            return False

    def ready(found):
        w = wipes[found.k]

        def rebuild(state_, frm, prior):
            return build_with(kin, state_, w, start=frm, prior=prior)
        return found.plan, rebuild, {"wipe_stroke": {"around": _Sampling}, "wipe_return": {"around": _Sampling},
                                     "wipe_back": {"after": lambda r: check_held(r, "wipe", open_hand=False, side=side)}}

    def done():
        cov = float(ctx["covered"].mean())
        memory(rig)["wiped"][support] = max(cov, memory(rig)["wiped"].get(support, 0.0))
        a, b = ctx["w"]["strip"]
        rig.log("wipe_result", tool=tool, support=support, hand=side, coverage=round(cov, 3),
                strip=[np.round(a, 3).tolist(), np.round(b, 3).tolist()])
        if cov < WIPE_COVER:
            raise SkillFailure(f"wipe {support}: contact coverage {cov:.2f}")
        return cov
    return Job(problem=problem, no_park=no_park, found=found_park, ready=ready, done=done)
