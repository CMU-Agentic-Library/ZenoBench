"""The set-down's job (motion_skills.Job): the carry posture first, the park search's problem, the plan to run after the drive, the result."""

from __future__ import annotations

import math
import numpy as np

from ..annotations import opening, rz
from ..evaluator import quat_R, tilt_deg
from ..kinematics import PAD_TIP
from ..park_search import Problem
from ..rig import FREE_SPACE_KW
from ..rig import SkillFailure
from ..primitives import query
from ..run import observe
from ..skill_plans import FREE_HAND, FREE_LOAD, PLACE_RELAY, T_of
from ..sticky import rest_R
from ..skills import (APPROACH_STEP, COM_MARGIN, EDGE_MIN_OVERHANG, PLACE_SPOT_COST, PLACE_TILTED_COST, PLACE_YAWS, PLACE_YAW_COST,
                      _edge_coord, _lowest_z, _open_edges, _overlaps_objects, _perp, check_held, pick_approach)
from ..tolerances import LEAVE_GAP, PLACE_LEVEL_MIN, PLACE_XY_TOL, PLACE_XY_TOL_CORNER, TARGET_TOL
from .carry import _carry_bottom_z, carry_posture
from .door_access import door_ahead, front_of, leave_tier

# an edge hold (a flat load pinched at its thickness: a book, a notebook, a tray held at its side): its gripped face
# set down over an open edge of the support (_edge_goals)
EDGE_STEP = 0.03          # m between positions along an edge (inherited: place_flat's)
EDGE_LEVEL = 0.03         # m between the overhang levels of a position...
EDGE_LEVELS = 2           # ...this many, the least overhang first
EDGE_SPOTS = 24           # positions x levels kept over all open edges, best first (11-07: 4 were too few)
EDGE_LEVEL_COST = 0.05    # m of park cost per level past the least overhang
EDGE_TILT_MAX = 20.0      # deg: an edge-held load left tilted more is not placed (inherited: place_flat's)
EDGE_PUSH_IN = 0.01       # m: then pushed on until its gripped face is this far inside the edge (place_flat's push)
EDGE_FINGER_CLEAR = 0.02  # m: the lower fingertip at least this far past the annotated edge -- the real top reaches a
#                           bit beyond it and a straight's check has no margin (cuRobo's constraint, activation
#                           distance 0): set down with the tip 5 mm past it, the centring touched the table (T01
#                           11-15).  With the TCP 2.5 cm in, the 6.5 cm of place_flat's EDGE_PLACE_OVERHANG


def square_yaws(q_obj):
    """The wrist turns (deg about the vertical) of a place that squares the object to the support's axes (square,
    HAND_PLAN 9f): from its yaw as the hand holds it now (quaternion w, x, y, z) -- a turn measured before the pick
    drifted with the carry (T06) -- the turns that leave its yaw on an axis, 0 / +-90 / 180 from the nearest."""
    w, x_, y_, z_ = q_obj
    yaw = math.degrees(math.atan2(2 * (w * z_ + x_ * y_), 1 - 2 * (y_ * y_ + z_ * z_)))
    err = (yaw + 45.0) % 90.0 - 45.0
    return tuple(round(k - err, 2) for k in (0.0, 90.0, -90.0, 180.0))


def place_job(rig, args, state, skill=None):
    """motion_skills.Job of the set-down: the carry posture settled for the support's rim first
    (carry_posture), every spot x hold x wrist turn one goal of the park search (the whole place
    planned there, skill_plans.plan_place, the goal the object's pose); after the drive the plan run
    with the place's hooks (run builds it again when the hold no longer gives its set-down pose:
    primitives.holds); then the result judged."""
    from ..motion_skills import Job
    name, s, spots, tray = args["name"], args["support"], args["spots"], args.get("tray")
    side = rig.hand_of(name)                       # the hand that holds it (HAND_PLAN 9c)
    if side is None:
        raise SkillFailure(f"place {name}: not held")
    kin, held_d = rig.arm_kin(side), rig.held_by(side)
    # behind a door (a shelf inside a cabinet, the fridge): open enough to reach past it, checked
    # before anything moves -- as the pick behind a door (door_access.door_ahead)
    door = None if tray else door_ahead(rig, s, None, f"place {name}")
    plan_place = skill.build if skill is not None else _plan_place()
    asset = rig.ann.asset_of(rig.ann.objects[name])
    # the carry posture of the drive to the park, before the park search checks it there -- not for an
    # edge hold: it drives in the posture it came in (as place_flat did; raised to the support's top
    # beside a bookcase the arm stopped 0.5 m short, T26 whose 11-15)
    edge = held_d["kind"] == "edge"
    clear_z = _carry_bottom_z(rig, tray or s["name"])
    carry_bottom_z = max(s["z"] + 0.03, clear_z or 0.0)
    if not edge:
        carry_posture(rig, min_bottom_z=carry_bottom_z, side=side)
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
    tcp, R_tcp = kin.tcp(rig.chain_q(side))
    relations = [(tcp - p_obj, R_tcp, None, float(p_obj[2] - _lowest_z(rig, name, st)))]
    over = math.degrees(math.acos(max(-1.0, min(1.0, float(R_obj[2, 2])))))
    if held_d["kind"] != "corner" and over > PLACE_LEVEL_MIN:
        R_lvl = rest_R(q_obj) @ R_obj.T
        relations.insert(0, (R_lvl @ (tcp - p_obj), R_lvl @ R_tcp, round(over, 1),
                             -float(asset["origin_to_bottom_center"][2])))
    if door is not None and _lies_on_a_face(asset) and not edge:
        # behind a door a box may also go in on another face: hand and load turned a quarter about one of
        # the hand's horizontal axes -- the fingers' closing axis (they stay on its sides) or the one across
        # it (they end above and below it, as on a plate) -- so a top pinch's way out becomes horizontal,
        # through the opening (leave_tier ranks it first), where a load held from above has no room under
        # the shelf above (11-13: a snack carton under cabinet_6's).  Both senses of each: the collision
        # check decides (the camera below the TCP; a finger under the load, in the shelf) -- also a load
        # stood on its longest axis (the user, 11-13: some go in only that way).  Not in the open (there it
        # goes down as it hangs, or levelled), nor for what rolls or holds something (asset.round grasps, a
        # container).
        R_base = R_lvl if relations[0][2] is not None else np.eye(3)
        relations += [_on_side(asset, R_base, R_obj, tcp - p_obj, R_tcp, axis, sign) for axis in (1, 0)
                      for sign in (1.0, -1.0)]
    search_near, prefer = rig.base_pose(), ()
    if math.hypot(search_near[0] - spots[0][0], search_near[1] - spots[0][1]) > 1.0:
        # far from the target: rank parks by reach to the target, not by
        # distance from here (all tries were spent near a corner 1.4 m away)
        search_near = None
    if door is not None:
        # the pose the open left the robot in biases the search toward the hinge: a park in front of
        # the door's free edge first, the pose now not tried first (the pick behind a door, alike)
        prefer = (front_of(rig, door, (spots[0][0], spots[0][1], s["z"])),)
        search_near = None if search_near is None else search_near[:2]
    # the set-down poses (the relay pose): every spot, relation and wrist turn is one goal -- for an
    # edge hold every position and overhang over an open edge and relation, the hand square to the edge
    edges = None                            # an edge hold: per goal, (the edge's outward normal, the overhang)
    yaws = PLACE_YAWS
    if args.get("square"):
        yaws = square_yaws(q_obj)
    if edge:
        goals, leg_sets, cost, edges = _edge_goals(rig, name, s, relations, args.get("hint"), st, held_d)
        if not goals:
            raise SkillFailure(f"place {name}: no free edge spot on {s['name']}")
    else:
        goals, leg_sets, cost = [], [], []
        for rank, spot in enumerate(spots):
            for off0, R0, levelled, hang in relations:
                body = np.array([spot[0], spot[1], s["z"] + hang + LEAVE_GAP])
                for deg in yaws:
                    Rz = rz(math.radians(deg))
                    goals.append((spot, Rz @ R0, levelled, deg, hang))
                    leg_sets.append([(body + Rz @ off0, Rz @ R0, FREE_SPACE_KW)])
                    cost.append(PLACE_SPOT_COST * rank + PLACE_YAW_COST * abs(deg) / 45.0 +
                                (PLACE_TILTED_COST if levelled is None and len(relations) > 1 else 0.0))
    # the hand opens to the grasp's width (an edge hold too: opened to FINGER_OPEN a finger went 1 mm into the
    # table's edge, T01 11-15); an edge hold's box in its box frame, which the open pads are moved clear of
    # before they pull out, as far as they need (plan_place)
    open_w = float(held_d.get("pre_open", 0.04))
    edge_box = _box_extent(kin, name) if edge else None
    # inside a cavity closed on five sides (the microwave): out through its opening before the tuck (plan_place)
    cavity = None if door is None or not door.get("cavity_aabb") else \
        {"box": tuple(door["cavity_aabb"]), "out": opening(door), "load": _box_extent(kin, name)}
    on = _set_down_on(s)
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
                          obj=name, on=on, edge_box=edge_box, cavity=cavity)
    # behind a door: the set-downs whose pull-out (back along the gripper axis) leaves straightest
    # through the opening built first (door_access.leave_tier; the pick behind a door takes the most
    # outward grasp first) -- else the 60 builds went on wrist turns with the hand in the back wall
    tiers = () if door is None else tuple(leave_tier(door, ls[0][1][:, 2]) for ls in leg_sets)
    problem = Problem(tuple(((ls[0][0],), (ls[0][0], ls[0][1]), c) for ls, c in zip(leg_sets, cost)), build,
                      PLACE_RELAY, near=search_near, prefer=prefer, tiers=tiers,
                      relay_free=FREE_LOAD if door is not None else None, label=f"place {name}", hand=side)
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
        ctx["kind"] = held_d["kind"]
        ctx["edge"] = None if edges is None else edges[found.k]
        return _place_ready(rig, name, s, targets[found.k], open_w, found.plan, plan_place, edge_box, side, cavity)

    def done():
        ok = _place_result(rig, name, s, ctx["spot"], ctx["kind"], tray)
        # an edge hold: the edge it was set down over and how far it overhangs (skills.place pushes it on)
        return {"edge": ctx["edge"]} if ctx["edge"] is not None else ok
    # the drive keeps the posture carry_posture settled above: it does not try the higher ride again (an
    # edge hold: the posture it came in)
    return Job(problem=problem, no_park=no_park, found=found_park,
               travel={"raise_load": False} if edge else {"min_bottom_z": carry_bottom_z, "raise_load": False},
               ready=ready, done=done)


def _edge_goals(rig, name, s, relations, hint, st, held=None):
    """The set-down goals of an edge hold (a flat load pinched at its thickness, the fingers above and
    below it): its gripped face over an open edge of ``s``, the hand square to it (approaching -n), at
    each position along the edge (EDGE_STEP, clear of its ends) and each overhang from the least that
    leaves the lower fingertip EDGE_FINGER_CLEAR past the edge (the TCP ``depth`` inside the face,
    PAD_TIP beyond it; not less than EDGE_MIN_OVERHANG) up to the most that keeps the centre of mass
    COM_MARGIN on the support (it is pushed on afterwards: the overhang is the fingers' room) -- where the
    load's footprint is free of other objects.  An object's top (a stack) or a container's rim (cover): every
    edge may be hung over, the object itself is not in the way (the furniture it stands on lies lower, under the overhang;
    the plan's checks decide).  Ranked by the distance to ``hint`` (else to the robot) and on shelving
    the middle of its long edge, as place_flat was; EDGE_SPOTS of them, each with every relation.
    (goals, leg_sets, costs) as place_job's, and per goal (the edge's outward normal, the overhang):
    skills.place pushes the load on from there.  ``held``: the hold (default the right hand's)."""
    held = held or rig.held
    h, depth, lat_half = float(held["h"]), float(held["depth"]), float(held["lat_half"])
    size = rig.ann.asset_of(rig.ann.objects[name])["size"]
    x0, y0, x1, y1 = s["aabb_xy"]
    # an object's top (a stack) or a container's rim (cover: a plate, held at its edge, laid on a pot) -- the
    # object under it is not in the way and every edge may be hung over (the plate in T15: "no free edge spot
    # on rim:handled_cooking_pot", 3/3, while the pot under the rim counted as an obstacle)
    top = s.get("category") in ("object_top", "rim")
    skip = {name, str(s["name"]).split(":", 1)[1]} if top else {name}
    if s.get("category") == "rim":
        # what is in the container lies under its rim, not in the lid's way (T09 lid_missing 11-26: the two
        # tomatoes in the pot ruled out every edge spot)
        under = str(s["name"]).split(":", 1)[1]
        skip |= {o for o in rig.ann.objects if o not in skip and rig.geo.inside(o, under, st)[0]}
    edges = [np.array(d, float) for d in ((1, 0), (-1, 0), (0, 1), (0, -1))] if top else _open_edges(rig, s)
    open_dirs = [tuple(np.round(d, 3)) for d in edges]
    # the overhang: at least the fingertip past the edge (LEAVE_GAP, nor less than EDGE_MIN_OVERHANG), at most the
    # centre of mass COM_MARGIN on the support; from EDGE_FINGER_CLEAR past it -- or, a short load that does not
    # leave that, the most its centre allows (the foil tray: no level at all with the 2 cm, T07 11-15)
    least = max(depth + PAD_TIP + LEAVE_GAP, EDGE_MIN_OVERHANG)
    most = h - COM_MARGIN
    start = min(max(depth + PAD_TIP + EDGE_FINGER_CLEAR, EDGE_MIN_OVERHANG), most)
    levels = [start + i * EDGE_LEVEL for i in range(EDGE_LEVELS) if least <= start + i * EDGE_LEVEL <= most]
    bx, by, _ = rig.base_pose()
    cands = []
    for n in edges:
        lat = _perp(n)
        e = _edge_coord(s, n)
        span = (x1 - x0) if abs(n[0]) > 0.5 else (y1 - y0)
        # 4 cm from an end that is closed (a raised side panel caught a book released at the very end of a
        # bookcase top), 1 cm from an open one (place_flat's)
        ax = np.array([0.0, 1.0]) if abs(n[0]) > 0.5 else np.array([1.0, 0.0])
        m_lo = 0.01 if tuple(np.round(-ax, 3)) in open_dirs else 0.04
        m_hi = 0.01 if tuple(np.round(ax, 3)) in open_dirs else 0.04
        lo_l = (y0 if abs(n[0]) > 0.5 else x0) + lat_half + m_lo
        hi_l = (y1 if abs(n[0]) > 0.5 else x1) - lat_half - m_hi
        if top:
            # a stack: the load may reach past the sides of what it is stacked on, its centre of mass
            # COM_MARGIN on it (a paperback larger than the book under it had no position at all, T14 11-15)
            lo_l = (y0 if abs(n[0]) > 0.5 else x0) + COM_MARGIN
            hi_l = (y1 if abs(n[0]) > 0.5 else x1) - COM_MARGIN
        for l in (np.arange(lo_l, hi_l + 1e-6, EDGE_STEP) if hi_l >= lo_l else []):
            edge_pt = n * e + np.abs(lat) * l
            for k, over in enumerate(levels):
                if (h - over > span - COM_MARGIN) if top else (2 * h - over > span + 0.02):
                    continue                                     # its centre (a stack) / far end past the far side
                c = edge_pt - n * (h - over)                     # the load's centre
                half = np.abs(n) * h + np.abs(lat) * lat_half
                box = [c[0] - half[0], c[1] - half[1], c[0] + half[0], c[1] + half[1], s["z"] + 0.005, s["z"] + size[2]]
                if _overlaps_objects(rig, box, skip, st, margin=0.02):
                    continue
                score = math.hypot(c[0] - hint[0], c[1] - hint[1]) if hint is not None else \
                    0.3 * math.hypot(c[0] - bx, c[1] - by)
                if "bookcase" in str(s.get("category", "")).lower():
                    # on shelving: the long (front) edge, away from its ends (a book slid in over the short side
                    # or next to a side panel stalled)
                    edge_len = (y1 - y0) if abs(n[0]) > 0.5 else (x1 - x0)
                    score += 0.5 * abs(l - 0.5 * (lo_l + hi_l)) + (0.4 if edge_len < 0.8 * max(x1 - x0, y1 - y0) else 0.0)
                cands.append((score + EDGE_LEVEL_COST * k, k, n, edge_pt, over))
    cands.sort(key=lambda t: t[0])
    goals, leg_sets, cost, edges = [], [], [], []
    for rank, (_, k, n, edge_pt, over) in enumerate(cands[:EDGE_SPOTS]):
        tcp_xy = edge_pt + n * (over - depth)                    # the TCP ``depth`` inside the gripped face
        for off0, R0, levelled, hang in relations:
            a = -R0[:, 2]                                        # the hand's approach (kinematics.gripper_rot)
            deg = (math.degrees(math.atan2(-n[1], -n[0]) - math.atan2(a[1], a[0])) + 180.0) % 360.0 - 180.0
            Rz = rz(math.radians(deg))
            o = Rz @ off0
            spot = (float(tcp_xy[0] - o[0]), float(tcp_xy[1] - o[1]))
            body = np.array([spot[0], spot[1], s["z"] + hang + LEAVE_GAP])
            goals.append((spot, Rz @ R0, levelled, round(deg, 1), hang))
            leg_sets.append([(body + o, Rz @ R0, FREE_SPACE_KW)])
            cost.append(PLACE_SPOT_COST * rank + EDGE_LEVEL_COST * k +
                        (PLACE_TILTED_COST if levelled is None and len(relations) > 1 else 0.0))
            edges.append((np.asarray(n, float).copy(), float(over)))
    return goals, leg_sets, cost, edges


def _box_extent(kin, name):
    """(lo, hi) of ``name``'s collision box in its box frame (Motion._box_of: the frame of its first collider)."""
    if kin.motion is None:
        return np.zeros(3), np.zeros(3)
    _, lo, hi = kin.motion._box_of(name)
    return np.asarray(lo, float), np.asarray(hi, float)


def _lies_on_a_face(asset):
    """A box: it rests on any face -- none of its grasps round, no container profile or tag."""
    return not (asset.get("container") or "container" in asset.get("tags", ())
                or any(g.get("round") for g in asset.get("grasps", ())))


def _on_side(asset, R_base, R_obj, off, R_tcp, axis, sign):
    """The relation (TCP minus origin, TCP rotation, label, origin above the lowest point) of the hold
    turned ``sign`` quarter about the hand's axis ``axis`` (R_tcp's column after R_base, the levelling:
    1 the fingers' closing axis, 0 the one across it), then levelled (the body axis nearest the vertical
    turned onto it, as sticky.rest_R: a load hanging a few degrees off lands flat)."""
    from scipy.spatial.transform import Rotation
    a = (R_base @ R_tcp)[:, axis]
    Q = Rotation.from_rotvec(sign * 0.5 * math.pi * a / np.linalg.norm(a)).as_matrix() @ R_base
    Rn = Q @ R_obj
    i = int(np.argmax(np.abs(Rn[2])))
    up = Rn[:, i] * np.sign(Rn[2, i])
    ax = np.cross(up, [0.0, 0.0, 1.0])
    if float(np.linalg.norm(ax)) > 1e-9:
        L = Rotation.from_rotvec(ax / np.linalg.norm(ax) * math.atan2(np.linalg.norm(ax), float(up[2]))).as_matrix()
        Q, Rn = L @ Q, L @ Rn
    size = np.asarray(asset["size"], float)
    centre = np.asarray(asset["origin_to_bottom_center"], float) + np.array([0.0, 0.0, 0.5 * size[2]])
    lowest = float((Rn @ centre)[2] - np.abs(Rn[2, :]) @ (0.5 * size))
    return Q @ off, Q @ R_tcp, f"turned{'yx'[axis == 0]}{'+' if sign > 0 else '-'}", -lowest


def _set_down_on(s):
    """The entity a set-down on support ``s`` lets the load touch as it is let go (release_spec): the
    furniture or object the support belongs to ("kitchen_cabinet_6/top", "rim:handled_cooking_pot")."""
    return str(s["name"]).split(":", 1)[-1].split("/", 1)[0]


def _plan_place():
    from ..skill_plans import plan_place
    return plan_place


def _place_ready(rig, name, s, goal, open_w, plan, plan_place=None, edge_box=None, side="right", cavity=None):
    """The place's plan to run (run.run) to set ``name`` down with its box frame at ``goal`` (the
    park search's plan: a set-down pose the hold no longer gives has run build it again,
    primitives.holds), its builder for the rest, its hooks.  Between the segments the place's own steps:
    the reach checked, the release logged and the load no longer held.  ``edge_box``: an edge hold's
    (plan_place: after it landed, as the place_landed anchor reads it, the pads moved clear of it).  ``side``:
    the hand that sets it down (HAND_PLAN 9c).  ``cavity``: inside a microwave's cavity (plan_place)."""
    kin = rig.kin if side == "right" else rig.left_kin
    plan_place = plan_place or _plan_place()
    out_len, rests = pick_approach(), (kin.rest, kin.drive)
    on = _set_down_on(s)

    def rebuild(state, frm, prior):
        return plan_place(kin, state, goal, open_w, out_len, rests, start=frm, prior=prior, step=APPROACH_STEP,
                          obj=name, on=on, edge_box=edge_box, cavity=cavity)

    def before_pull_out(rig):
        # let go, it may have settled against a finger: allowed on the pull-out, recorded -- a query
        # of the State now with the fingers in the model (primitives.query), nothing changed
        st = observe(rig)
        with query(kin, st, FREE_HAND):
            if kin.scene is not None and not kin.free(st.q(kin.side)):
                rig.log("place_pull_out_touching", obj=name, why=kin.explain(st.q(kin.side)))

    def after_down(rig):
        # the hand against where the set-down sent it (Rig._settle measured it as the set-down stopped; run
        # judges every segment by the same, after this hook): whether the hold still gives that pose was
        # checked before the set-down ran (primitives.holds, PLACE_TOL)
        err = rig.last_off
        if err > TARGET_TOL:
            # the set-down is checked free all the way: stopped short, something is in the way
            raise SkillFailure(f"place {name}: the set-down stopped {err:.3f} m short of its pose")
        check_held(rig, "place_down", open_hand=False, side=side)
        rig.caption = f"PLACE {name}: release"
        before_release, _ = rig.obj_pose(name)
        rig.log("place_before_release", obj=name, pos=np.round(before_release, 4).tolist(),
                gap_m=round(float(_lowest_z(rig, name, rig.state())) - float(s["z"]), 4))

    def after_release(rig):
        after_open, _ = rig.obj_pose(name)
        rig.log("place_after_open", obj=name, pos=np.round(after_open, 4).tolist())
        setattr(rig, "held" if side == "right" else "left_held", None)

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
    if kind == "edge":
        # set down over the edge, not at a spot: on the support and lying flat (place_flat's judgement)
        on, why = rig.geo.on(name, s["name"], st)
        tilt = tilt_deg(st["objects"][name]["quat"])
        rig.log("place_result", obj=name, support=s["name"], on_support=bool(on), tilt_deg=round(tilt, 1), detail=why)
        if not on or tilt > EDGE_TILT_MAX:
            raise SkillFailure(f"place {name} on {s['name']}: {why}, tilt {tilt:.0f} deg")
        return True
    if tray is not None:
        ok, why = rig.geo.inside(name, tray, st)
        rig.log("place_result", obj=name, container=tray, inside=bool(ok), detail=why)
        if not ok:
            raise SkillFailure(f"place {name} in {tray}: {why}")
        return True
    # the lowest point as it lies (Geometry.resting): an object set down on another face (behind
    # a door, _on_side) has its own bottom face on its side
    b = rig.geo.resting(name, st)
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
    tol = PLACE_XY_TOL_CORNER if kind == "corner" else PLACE_XY_TOL   # a corner-held object pivots flat on release
    if not (on and err < tol):
        raise SkillFailure(f"place {name}: xy err {err:.3f} m, on support {on} ({why})")
    return True
