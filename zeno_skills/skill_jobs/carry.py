"""The carry constraints and the carry posture (docs/MOTION_ARCHITECTURE.md 6, navigate; 9.3 step 1.3)."""

from __future__ import annotations

import math
import numpy as np

from ..motion_state import Failure
from ..rig import SkillFailure
from ..run import observe
from ..run import run
from ..skills import (CARRY_Z, _carry_floor, _carry_goal_set, check_held)
from ..tolerances import CARRY_LOW_TOL, CARRY_SUPPORT_Z
from .base import RigBase


CARRY_FRONT_X = (0.25, 0.55)  # m: base-frame TCP x of a carry posture (CARRY_SPOTS' 0.35-0.45, 0.10 either way)


CARRY_FRONT_Y = (-0.40, 0.00) # m: ...and y (CARRY_SPOTS' -0.30 - -0.10, 0.10 either way)


CARRY_LOW_COST = 1.0          # m-equivalent cost of a carry goal below the height a destination asks for


def _carry(rig, name, min_bottom_z=None):
    """skill_plans.Carry for ``name`` in the right hand: the constraints a posture to drive in meets
    (docs/MOTION_ARCHITECTURE.md 6, navigate) -- the load in front of the body near its centre line
    (CARRY_FRONT_*: held out to the side, objects caught on door frames), its bottom no lower than
    CARRY_Z, the whole robot clear where it stands in that posture (poses_clear) -- and the carry
    goal set when it does not.  ``min_bottom_z`` (a destination's rim, _carry_floor) is a wish, not a
    constraint: the load is raised to it where a carry goal that high is reachable, else rides as it
    is (the drive's whole-body plan checks it against the world; 11-08 T07 / T23: 1.15-1.18 m out of
    reach, the old _carry_pose kept the posture there too)."""
    from ..skill_plans import Carry, held_frame
    from ..primitives import PoseSet
    from .. import base_planner
    kin, base = rig.kin, RigBase(rig)
    floor = _carry_floor(rig, name, min_bottom_z)
    frame, lo, hi = kin.motion._box_of(name) if kin.motion is not None else (None, None, None)
    corners = None if lo is None else \
        np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])

    def check(state):
        q = state.q(kin.side)
        tcp, _ = kin.tcp(q)
        x, y, yaw = state.base
        c, s_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        lx, ly = c * (tcp[0] - x) + s_ * (tcp[1] - y), -s_ * (tcp[0] - x) + c * (tcp[1] - y)
        if not (CARRY_FRONT_X[0] <= lx <= CARRY_FRONT_X[1] and CARRY_FRONT_Y[0] <= ly <= CARRY_FRONT_Y[1]):
            return f"the load is not in front of the body (TCP at {lx:.2f}, {ly:.2f} m in the base frame)"
        held = state.held(kin.side)
        bottom = _bottom(state, q)
        if bottom is not None and bottom < CARRY_Z - CARRY_LOW_TOL:
            return f"the load's bottom at {bottom:.3f} m is below {CARRY_Z:.3f} m"
        if kin.motion is not None and base.depths(state, [tuple(state.base)])[0] > base_planner.DEPTH_TOL:
            return "the robot is not clear where it stands in this posture"
        return None

    def _bottom(state, q):
        held = state.held(kin.side)
        if corners is None or held is None:
            return None
        T = held_frame(kin, q, held)
        return float((corners @ T[:3, :3].T + T[:3, 3])[:, 2].min())

    def want(state):
        bottom = _bottom(state, state.q(kin.side))
        if floor <= CARRY_Z or bottom is None or bottom >= floor - CARRY_LOW_TOL:
            return None
        return f"the load's bottom at {bottom:.3f} m is below the {floor:.3f} m asked"

    low, high = _carry_goal_set(rig, name), _carry_goal_set(rig, name, min_bottom_z)

    def goals(state, q):
        # the constraints broken: the carry goal set from CARRY_Z up, the heights asked first
        (g_lo, how), (g_hi, _) = low(state, q), high(state, q)
        if floor <= CARRY_Z:
            return g_lo, how
        return PoseSet(g_hi.goals + g_lo.goals, tuple(g_hi.cost) + tuple(c + CARRY_LOW_COST for c in g_lo.cost),
                       g_lo.prefer, g_lo.weights), how
    return Carry(check, goals, want, high)


def _carry_bottom_z(rig, place):
    """Height a carried load's bottom should keep while driving to ``place``:
    3 cm above the destination surface (raised at the start of the drive, not
    beside the counter where a late lift scraped a mug off its edge)."""
    from ..predicates import entity_kind
    kind, rec = entity_kind(rig.ann, place)
    z = None
    if kind == "support":
        z = float(rec["z"])
    elif kind in ("furniture", "appliance", "articulated"):
        zs = [s["z"] for s in rig.ann.supports if (s.get("furniture") == place or s["name"].startswith(place + "/"))
              and CARRY_SUPPORT_Z[0] <= s["z"] <= CARRY_SUPPORT_Z[1]]
        z = max(zs) if zs else None
    elif kind == "object":
        st = rig.state()
        a = rig.ann.asset_of(rec)
        if a.get("container"):
            # going to a container (pour, drop): carry above its rim
            z = float(rig.geo.bottom(place, st)[2]) + float(a["container"]["rim_height"])
        else:
            sup = rig.geo.support_under(place, st)
            z = float(sup["z"]) if sup is not None else None
    if z is None or z < CARRY_SUPPORT_Z[0] or z > CARRY_SUPPORT_Z[1]:
        return None                 # floor-level or out-of-reach heights keep the default carry
    if kind == "support" and rec.get("category") != "cabinet_inside" and "/inside" not in rec["name"]:
        # over the loose objects already standing there: the base drives in
        # along the counter and a load held 3 cm above the top swept a
        # rolling pin and a bottle (capped: tall items are passed by the arm)
        st = rig.state()
        names = {rec["name"]}
        tops = []
        for o in rig.ann.objects:
            if rig.held is not None and o == rig.held["name"]:
                continue
            sup = rig.geo.support_under(o, st)
            if sup is not None and sup["name"] in names:
                tops.append(float(rig.geo.bottom(o, st)[2]) + float(rig.ann.asset_of(rig.ann.objects[o])["size"][2]))
        if tops:
            z = max(z, min(max(tops), z + 0.12))
    return round(z + 0.03, 3)


def carry_posture(rig, min_bottom_z=None, label="carry_in"):
    """With a load in the right hand: the posture checked against the carry constraints (_carry) and
    kept when it meets them -- pick's carry_in chose it -- else planned to the carry goal set
    (free space, the tilt held), SkillFailure when there is none (no unchecked straight, no posture
    kept that fails them: docs 9.3 step 1.3).  plan_navigate's first stage, run on its own: a skill
    that settles the posture before its park search (place, a stand-off check)."""
    if rig.held is None:
        return
    from ..skill_plans import plan_navigate
    state = observe(rig)
    plan = plan_navigate(rig.kin, rig.left_kin, state, None, None, carry=_carry(rig, rig.held["name"], min_bottom_z),
                         stop="arm")
    if isinstance(plan, Failure):
        raise SkillFailure(f"{label}: {plan.why}")
    rig.log("carry_posture", how=plan.info.get("carry"), moved=bool(plan.segments))
    from ..skill_plans import plan_clear
    run(rig, plan, None, {"carry_in": {"after": lambda r: check_held(r, "carry_in", open_hand=False)}},
        clear=lambda st, what: plan_clear(rig.kin, st, **what))
