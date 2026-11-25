"""Annotation-driven Zeno Malo skills.  Nothing here is asset-specific: every
number comes from annotations/<scene>.json + annotations/assets.json.

    navigate(rig, (x, y, yaw))
    open_articulated(rig, name) / close_articulated(rig, name)   doors and drawers
    pick(rig, name)          pinch grasp (top / rim), or push-then-edge-pinch for
                             flat objects wider than the gripper; floor objects
                             with the torso lowered
    place(rig, name, "in:<container>")        drop into a container
    place_on(rig, name, support, hint_xy)     free spot on a support surface
                             (edge-held flat objects go back over a free edge)

Each skill measures its own success from simulator state (joint angle, object
pose, finger gap) and raises SkillFailure otherwise.
"""

from __future__ import annotations

import math
from contextlib import contextmanager, nullcontext

import numpy as np
from scipy.spatial.transform import Rotation

from .annotations import rz
from .clearance import FREE, FREE_ELSE_STRAIGHT, LEAVE_CONTACT, LEGACY, closing, lifting
from .evaluator import quat_R
from .kinematics import PAD_TIP, finger_model_box, finger_model_length, gripper_rot
from .physics import CONTAINER_BASE_T, CONTAINER_WALL, PHYSICS_HZ
from .motion_state import Failure, at_base, clearing, with_arm, with_width
from .rig import (FINGERS_KW, FREE_SPACE_KW, HINT_REACH, HINT_TURN, LEAVE_GAP, LEAVE_MARGIN, ON_LINE, Dropped,
                  SkillFailure)
from .park_search import Problem
from .run import observe, run
from .skill_plans import plan_pick, plan_place
from .sticky import note_grasp, rest_R, welded
from .tolerances import (DOOR_CLOSED_TOL, DOOR_OPEN_TOL, DRAWER_OPEN_FRAC, HELD_LOST_GAP, HELD_SHIFT_GAP,
                         HELD_SHIFT_MAX, HELD_SLIP, PICK_LIFT_FRAC, PICK_RISE_MIN, RIDE_DONE_PRIS, RIDE_DONE_REV,
                         SAME_POSTURE, SHUT)

TCP_BACKOFF = 0.12   # the old handle paths' pre-grasp (_handle_targets); the door framework has DOOR_REACH_IN
EDGE_MIN_OVERHANG = 0.055     # below this the lower finger hits the support edge
COM_MARGIN = 0.015            # centre of mass stays at least this far inside the edge while overhanging (3.5 cm until
                              # 11-13: objects under 18 cm long -- a tissue box, a rice container -- had no edge at all)
CARRY_Z = 0.55                # carried objects ride at least this high (floor picks)
APPROACH_STEP = 0.003         # m between the waypoints of a reach-in / set-down straight (the search's plan and its execution)
PICK_LEAVE_CHECK = 0.03       # m of the lift out of the grasp the park search checks (the contact exit takes <= 3 cm)
# m: the lowest pad corner of a top pinch stays this far above the surface under the object (the
# vertical pinch's former TCP rule of 2.2 cm above its bottom, less PAD_TIP: 2.15 mm)
PAD_FLOOR_GAP = 0.022 - PAD_TIP


# ---------------------------------------------------------------- navigation
AT_PARK_M = 0.02              # m and deg: a base this close to a park is at it (no drive); inherited, unmeasured
AT_PARK_DEG = 2.0
BLOCKED_PROBE_M = 0.4         # m toward the goal a blocked base plan is probed at, per posture (diagnostic only)
CARRY_SPOTS = ((0.35, -0.10), (0.40, -0.25), (0.45, -0.15), (0.45, -0.30))   # base-frame TCP xy, m
CARRY_SPOT_COST = 2.0         # rad of joint travel a carry spot 1 m off the first (the body's centre line) costs
CARRY_RISE = 0.15             # m: carry heights from the lowest allowed up to this much higher
CARRY_YAWS = 8                # hand turns about the world vertical tried at each carry spot (the load stays level)
CARRY_BODY_W = 3.0            # torso and waist off upright count this many times an arm joint's travel


def _carry_goals(base, tcp, R, z_lo, side="right"):
    """The carry goal set at base pose ``base`` (x, y, yaw_deg) for a load held at (tcp, R): the
    CARRY_SPOTS at heights from z_lo (the TCP's lowest) up, the hand turned about the world
    vertical in CARRY_YAWS steps; for the left hand the spots mirrored (y), as the arms are (HAND_PLAN
    9c, the user: the left mirrors the right's carry values).  (goals [(p, R)], cost per goal)."""
    my = 1.0 if side == "right" else -1.0
    zs = sorted({round(z, 3) for z in (z_lo, max(z_lo, tcp[2]), z_lo + CARRY_RISE)})
    x, y, yaw = base
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    turns = [Rotation.from_euler("z", 2 * math.pi * k / CARRY_YAWS).as_matrix() @ R for k in range(CARRY_YAWS)]
    goals, cost = [], []
    for lx, ly in CARRY_SPOTS:
        ly = my * ly
        for z in zs:
            for Rk in turns:
                goals.append((np.array([x + c * lx - s * ly, y + s * lx + c * ly, z]), Rk))
                cost.append(CARRY_SPOT_COST * math.hypot(lx - CARRY_SPOTS[0][0], ly - my * CARRY_SPOTS[0][1]))
    return goals, cost


def _hand_of(rig, name):
    """The hand that holds ``name`` ("right" / "left"), or None (Rig.hand_of; the tests' stand-ins too)."""
    for side, h in (("right", getattr(rig, "held", None)), ("left", getattr(rig, "left_held", None))):
        if h is not None and h.get("name") == name:
            return side
    return None


def _carry_ref(kin, q):
    """(posture, per-joint weights) the carry goal set's IK solutions are sought near and scored
    from: q with the body upright -- torso up, waist straight (a pick leaves them where it reached
    from; bent forward, the carry posture blocked every park beside the counter)."""
    upright = np.asarray(q, float).copy()
    upright[0], upright[1] = float(kin.hi[0]), 0.0
    return upright, np.r_[CARRY_BODY_W, CARRY_BODY_W, np.ones(len(upright) - 2)]


def _carry_floor(rig, name, min_bottom_z=None):
    """The lowest a carried load's bottom may ride: CARRY_Z (floor picks), or ``min_bottom_z`` (a
    rim the destination asks to clear) -- an edge-held book 6 cm more, its free end droops on the
    way (step 3c: the droop goes into the held object's model with the edge place)."""
    z = CARRY_Z
    if min_bottom_z is not None:
        side = _hand_of(rig, name)
        h = (rig.held if side == "right" else getattr(rig, "left_held", None)) if side else {}
        z = max(z, float(min_bottom_z) + (0.06 if h.get("kind") == "edge" else 0.0))
    return z


def _carry_goal_set(rig, name, min_bottom_z=None, side=None):
    """carry_goals for skill_plans.plan_pick / plan_navigate: at a State with ``name`` held and the
    hand at q, the carry goal set (CARRY_SPOTS from the base, heights from the load's bottom at
    _carry_floor up, the turns about the vertical), sought near the upright body (_carry_ref); a
    container on a rim pinch slower and smooth (it swings out of the pads on a fast sweep).  ``side``: the
    hand (default: the one that holds ``name``, else the right -- a pick's carry, before the close)."""
    from .primitives import PoseSet
    from .skill_plans import held_frame
    side = side or _hand_of(rig, name) or "right"
    kin = rig.kin if side == "right" else rig.left_kin
    frame, lo, hi = kin.motion._box_of(name)
    corners = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    rim = bool(rig.ann.asset_of(rig.ann.objects[name]).get("container"))
    floor = _carry_floor(rig, name, min_bottom_z)

    def carry_goals(state, q):
        held = state.held(kin.side)
        tcp, R = kin.tcp(np.asarray(q, float))
        T = held_frame(kin, q, held)
        hang = max(0.0, float(tcp[2] - (corners @ T[:3, :3].T + T[:3, 3])[:, 2].min()))
        goals, cost = _carry_goals(state.base, tcp, R, floor + hang, side)
        upright, weights = _carry_ref(kin, q)
        return PoseSet(tuple(goals), tuple(cost), upright, weights), \
            {"step": 0.005 if rim else 0.01, "steps_per_wp": 6 if rim else 4, "smooth": rim}
    return carry_goals


def check_held(rig, label, open_hand=True, side="right"):
    """Is the object in ``side``'s hand still there?  Its distance to that hand's TCP must match the one
    measured at the grasp and the fingers must not have shut.  A sticky-hands weld holds it: never dropped.
    Shifted in the pinch but still between the pads: re-anchored.  Dropped: the hand opened here
    (``open_hand``, the old entries' callers), or -- as a hook of a plan (run.run), which judges and does
    not move the robot -- the Dropped asks run for the failure exit that opens it (motion_state.clearing).
    One check for both hands (HAND_PLAN 9a: the left had no re-anchor and stayed shut on a drop)."""
    from .rig import _chain_q, _fingers_of, _held_of
    h = _held_of(rig, side)
    if h is None or welded(rig, side, h["name"]):
        return
    kin = rig.kin if side == "right" else rig.left_kin
    tcp, _ = kin.tcp(_chain_q(rig, side))
    body, _ = rig.obj_pose(h["name"])
    slip = abs(float(np.linalg.norm(tcp - body)) - float(np.linalg.norm(h["tcp_minus_body"])))
    f = _fingers_of(rig, side)
    gap = float(f.sum())          # an off-centre rim pinch drives one finger to ~0 while holding
    if HELD_SLIP < slip < HELD_SHIFT_MAX and gap > HELD_SHIFT_GAP:
        # shifted in the pinch but still between the pads: re-anchor
        rig.log("held_shift", obj=h["name"], side=side, during=label, slip_m=round(slip, 3),
                fingers=f.round(4).tolist())
        h["tcp_minus_body"] = tcp - body
        return
    if slip > HELD_SLIP or gap < HELD_LOST_GAP:
        rig.log("dropped", obj=h["name"], side=side, during=label, slip_m=round(slip, 3),
                fingers=f.round(4).tolist(), at=[round(float(v), 3) for v in body])
        setattr(rig, "held" if side == "right" else "left_held", None)
        exc = Dropped(f"{label}: {h['name']} slipped out of the {'' if side == 'right' else 'left '}hand while carrying it")
        if not open_hand:
            raise clearing(exc, 0.04, leave=False, ticks=20, side=side)
        rig.grip(0.04, 20, side=side)
        raise exc


def check_both_held(rig, label, open_hand=True):
    """check_held for each hand that holds something."""
    for side in ("right", "left"):
        check_held(rig, label, open_hand=open_hand, side=side)


def right_hand_only(rig, name, verb):
    """For a skill still on the old entries (HAND_PLAN 2.2): ``name`` held in the left hand is a
    SkillFailure that says so -- not "not held", not the right hand's load used instead (HAND_PLAN 3.3)."""
    left = getattr(rig, "left_held", None)
    if left is not None and left["name"] == name and (rig.held is None or rig.held["name"] != name):
        raise SkillFailure(f"{verb}: {name} is in the left hand, and {verb} takes the right hand only until it is "
                           f"migrated (docs/motion/HAND_PLAN.md)")


def check_left_held(rig, label):
    """check_held of the left hand (kept for its callers)."""
    check_held(rig, label, side="left")


def navigate(rig, pose, label="navigate", min_bottom_z=None, arrive=None, raise_load=True):
    """Drive to ``pose`` (skill_plans.plan_navigate, run by motion_skills.run_skill): empty-handed
    the arm folds first where it stands when the arm planner finds a way (else where the base plan
    finds room) and drives folded, hanging both arms at the side only along the stretches the fold
    does not fit (the planner's choice, travel_chain); with a load in a hand its posture is checked
    against the carry constraints and kept, or planned to the carry goal set (``min_bottom_z``: a
    rim to clear), and the base drives slower (Rig.drive_base caps the speed by what the hands
    hold).  ``arrive``: the arm posture to arrive in instead of the fold (right-arm joints, or
    (right, left)).  ``raise_load`` False: the caller settled the carry posture for this
    ``min_bottom_z`` already (skill_jobs.carry.carry_posture) -- it is checked, not raised again."""
    from .motion_skills import SKILLS, run_skill
    return run_skill(rig, SKILLS["navigate"], {"pose": tuple(pose), "label": label, "min_bottom_z": min_bottom_z,
                                               "arrive": arrive, "raise_load": raise_load})


def base_reachable(rig, poses):
    """Per base pose (x, y, yaw_deg): whether the column's inscribed circle can drive there from
    where the robot stands (RigBase.reachable)."""
    rig.sync_world()
    return _reachable(rig.world, rig.base_pose(), poses)


def _reachable(world, base, poses):
    """Per base pose (x, y, yaw_deg): whether the column's inscribed circle can drive there from
    ``base`` -- one field over all of them (base_planner.distance_field rooted at the robot; it is
    symmetric), the cheap test that base_planner.plan makes first, for a goal set.  Over the whole
    scene, as plan has it (relocate's area): a route may leave the box around the start and the
    poses (T12 s11: bookcase to desk_1 through the doorway)."""
    from . import base_planner as bp
    x, y = float(base[0]), float(base[1])
    cells = [(int(round((p[0] - x) / bp.RES)), int(round((p[1] - y) / bp.RES))) for p in poses]
    a = scene_area(world)
    bounds = (min(int(math.floor((a[0] - x) / bp.RES)), 0, *[c[0] for c in cells]),
              min(int(math.floor((a[1] - y) / bp.RES)), 0, *[c[1] for c in cells]),
              max(int(math.ceil((a[2] - x) / bp.RES)), 0, *[c[0] for c in cells]),
              max(int(math.ceil((a[3] - y) / bp.RES)), 0, *[c[1] for c in cells]))
    D, i0, j0 = bp.distance_field(world.circles_clear, (x, y), (0, 0, 0), bounds, (0, 0, 0))
    return reached_cells(D, i0, j0, cells)


def reached_cells(D, i0, j0, cells):
    """Per lattice cell: the field D reaches it or one of its 8 neighbours -- a goal cell counts as
    passable, as base_planner.plan has it (the goal pose is checked on its own; a park beside
    furniture may sit in a cell the inscribed circle does not clear)."""
    out = []
    for i, j in cells:
        win = D[max(0, i - i0 - 1):i - i0 + 2, max(0, j - j0 - 1):j - j0 + 2]
        out.append(bool(np.isfinite(win).any()))
    return out


def travel_postures(rig, arrive=None):
    """navigate's posture chain from the robot as it stands (skill_plans.travel_chain, the one
    source the park search's drive check uses too)."""
    from .skill_plans import travel_chain
    return travel_chain(rig.kin, rig.left_kin, observe(rig), arrive)


def posture_sets(rig, postures):
    """For base_planner.plan: (sphere sets per posture, per switch a few sets for the lattice,
    per switch the sets every DENSE of motion) of postures [(right, left)]."""
    from . import base_planner
    motion = rig.kin.motion
    sets = motion.body_spheres(rig, postures)
    switches, dense = [], []
    for (ra, la), (rb, lb) in zip(postures[:-1], postures[1:]):
        us = np.linspace(0, 1, base_planner.SWITCH_FINE)
        fine = motion.body_spheres(rig, [(ra + (rb - ra) * u, la + (lb - la) * u) for u in us])
        switches.append(fine[np.round(np.linspace(0, len(fine) - 1, base_planner.SWITCH_SAMPLES)).astype(int)])
        dense.append(base_planner.dense_sets(fine))
    return sets, switches, dense


def _rest_posture(rig):
    """(right, left) travel posture: each empty arm folded, an arm with a load as it is."""
    return (rig.kin.rest.copy() if rig.held is None else rig.q_cmd.copy(),
            rig.left_kin.rest[2:].copy() if rig.left_held is None else rig.left_q_cmd.copy())


def relocate(rig, goal, postures=(), label="relocate", **drive):
    """Move the base to ``goal`` (x, y, yaw_deg; None: as little as possible) on a whole-body plan
    (base_planner): the arms leave their current posture and pass through ``postures`` -- [(name,
    (right, left))] -- in order, each switch made where the base stands clear of everything with
    the arms anywhere between the two postures (a straight joint move).
    Nothing near the start or goal is exempt.  ``drive``: drive_base speeds.  SkillFailure when
    there is no such plan."""
    from .primitives import drive as drive_segment
    from .run import execute
    from .skill_jobs.base import RigBase
    seg = drive_segment(RigBase(rig), observe(rig), goal, list(postures), label, **drive)
    if isinstance(seg, Failure):
        raise SkillFailure(seg.why)
    execute(rig, seg)


def _base_plan(rig, goal, postures, label, state=None, quiet=False):
    """_base_steps, SkillFailure when there is no plan: ([base_planner.Step], the posture chain)."""
    steps, chain, why = _base_steps(rig, goal, postures, label, state, quiet)
    if steps is None:
        raise SkillFailure(why)
    return steps, chain


def _base_steps(rig, goal, postures, label, state=None, quiet=False):
    """The whole-body base plan from ``state`` (default: the robot as it stands): ([base_planner.Step],
    the posture chain, None), or (None, chain, why).  ``quiet``: no base_plan event, no probes of a
    blocked plan (the park search's drive check)."""
    from . import base_planner
    if state is None:
        rig.sync_world()
    motion = rig.kin.motion
    if motion is None:
        return None, [], f"{label}: no whole-body model (cuRobo) to plan the base with"
    q_r, q_l = (rig.q_cmd, rig.left_q_cmd) if state is None else state.posture().pair()
    origin = rig.base_pose() if state is None else tuple(state.base)
    chain = [("start", (np.asarray(q_r, float).copy(), np.asarray(q_l, float).copy()))]
    for name, (qr, ql) in postures:
        qr, ql = np.asarray(qr, float), np.asarray(ql, float)[-7:]
        if np.max(np.abs(qr - chain[-1][1][0])) < SAME_POSTURE and np.max(np.abs(ql - chain[-1][1][1])) < SAME_POSTURE:
            continue
        chain.append((name, (qr, ql)))
    sets, switches, dense = posture_sets(rig, [c[1] for c in chain])
    import time
    t0 = time.perf_counter()
    area = scene_area(rig.world)
    with motion.base_world(area[:2], area[2:]):
        steps, lat = base_planner.plan(lambda poses, sph: motion.base_depths(rig, poses, sph), origin,
                                       goal, sets, switches, area=area, footprint=rig.world.footprints_clear,
                                       passable=rig.world.circles_clear, dense_switches=dense)
    if quiet:
        return steps, chain, None if steps is not None else f"{label}: {lat.why}"
    rig.log("base_plan", target=label, goal=None if goal is None else [round(float(v), 3) for v in goal],
            postures=[c[0] for c in chain], poses_checked=lat.evaluated, found=steps is not None,
            expanded=getattr(lat, "expanded", 0), rounds=getattr(lat, "rounds", 0),
            seconds=round(time.perf_counter() - t0, 2),
            start_footprint=bool(rig.world.footprint_clear(*rig.base_pose()[:2], math.radians(rig.base_pose()[2]))),
            why=lat.why, tol0=round(lat.tol0, 4), visited=getattr(lat, "visited", None) if steps is None else None)
    if steps is None:
        hit = None
        if goal is not None and "goal pose" in (lat.why or ""):
            hit = motion.base_explain(rig, (goal[0], goal[1], math.radians(goal[2])), sets[-1])
        elif lat.tol0 > 0:
            x, y, yaw = rig.base_pose()
            hit = motion.base_explain(rig, (x, y, math.radians(yaw)), sets[0])
        if goal is not None:
            x, y, yaw = rig.base_pose()
            d = np.array(goal[:2]) - [x, y]
            p_ = np.array([x, y]) + d / max(np.linalg.norm(d), 1e-9) * BLOCKED_PROBE_M
            for m, (name, _) in enumerate(chain):
                rig.log("base_plan_probe", target=label, posture=name,
                        hit=motion.base_explain(rig, (p_[0], p_[1], math.radians(yaw)), sets[m]),
                        footprint=bool(rig.world.footprint_clear(p_[0], p_[1], math.radians(yaw))))
        rig.log("base_plan_blocked", target=label, hit=hit)
        return None, chain, f"{label}: {lat.why}" + (f" ({hit[0][0]} in {hit[0][1]} {hit[0][2]} mm)" if hit else "")
    return steps, chain, None


def poses_clear(rig, poses):
    """The base poses [(x, y, yaw_deg)] where the arms and what the hands hold stand clear of the
    world in the posture navigate arrives in (each empty arm folded, a loaded one as it is): goals
    the base planner accepts (the caller checks the footprint).  All of them without cuRobo."""
    from . import base_planner
    motion = rig.kin.motion
    if motion is None or not poses:
        return list(poses)
    rig.sync_world()
    d = motion.base_depths(rig, np.array([[x, y, math.radians(yaw)] for x, y, yaw in poses]),
                           motion.body_spheres(rig, [_rest_posture(rig)]))[0]
    return [p for p, dp in zip(poses, d) if dp <= base_planner.DEPTH_TOL]


def scene_area(world):
    """(x0, y0, x1, y1) the base may drive in: the annotated furniture's extent."""
    B = world.B[world.B[:, 2] > -0.5]
    return float(B[:, 0].min()), float(B[:, 1].min()), float(B[:, 3].max()), float(B[:, 4].max())


def plan_drive(rig, goal, label="drive"):
    """Waypoints [(x, y, yaw_deg)] after the start of a whole-body base path to ``goal`` with the
    arms as they are (for callers that drive it themselves); SkillFailure when there is none."""
    steps, _ = _base_plan(rig, goal, (), label)
    return [w for st in steps for w in st.path[1:]]


def straight_base_move(rig, target, label, **drive):
    """Drive straight to ``target`` (x, y, yaw_deg) -- a turn in place, a sidestep: the motion the
    caller asks for, not a search -- after checking the whole robot (arms as they are, what the
    hands hold, base column) along it; it may not sink deeper than it starts.  SkillFailure
    (nothing moves) when it is blocked.  primitives.drive_straight, run.execute."""
    from .primitives import drive_straight
    from .run import execute
    from .skill_jobs.base import RigBase
    seg = drive_straight(RigBase(rig), observe(rig), target, label, **drive)
    if isinstance(seg, Failure):
        raise SkillFailure(seg.why)
    execute(rig, seg)


def drive_to(rig, goal, label="drive_to", **drive):
    """The base to ``goal`` on a whole-body plan, the arms as they are (relocate)."""
    relocate(rig, goal, (), label=label, **drive)


def _travel_q(rig):
    """Arm posture while driving to a park: tucked, or the current carry pose."""
    return rig.kin.rest if rig.held is None else rig.q_cmd


def _goto_park(rig, park, min_bottom_z=None):
    x, y, yaw, _ = park
    if not _at_park(rig, x, y, yaw):
        navigate(rig, (x, y, yaw), min_bottom_z=min_bottom_z)


def _at_park(rig, x, y, yaw):
    """The base already at the park (_goto_park does not drive: the arm stays as it is)."""
    bx, by, byaw = rig.base_pose()
    return math.hypot(x - bx, y - by) <= AT_PARK_M and abs((yaw - byaw + 180) % 360 - 180) <= AT_PARK_DEG


def _grasp_of(name, g, T_obj):
    """skill_plans.plan_pick's grasp of candidate ``g`` (its TCP pose in the world) on ``name``, whose
    box frame stands at T_obj (the State's): the pose in that frame, the reach-in (_grasp_approach)
    in the TCP frame -- what the plan derives from the object wherever the State has it."""
    R = np.asarray(g["R"], float)
    T = np.eye(4)
    T[:3, :3], T[:3, 3] = R, np.asarray(g["p"], float)
    u, L = _grasp_approach(g)
    return {"name": name, "T_obj_tcp": np.linalg.inv(np.asarray(T_obj, float)) @ T,
            "u": R.T @ np.asarray(u, float), "L": float(L),
            "pre_open": float(g["pre_open"]), "kind": "edge" if g["kind"] == "thickness_pinch" else "pinch"}


def _handle_targets(rig, a, q, flip=False, tilt=0.0, grasp="side"):
    p, R, appr = rig.ann.handle_pose(a, q, grasp, flip, tilt)
    return p, R, appr, [(p - TCP_BACKOFF * appr + np.array([0, 0, 0.08]), R),
                        (p - TCP_BACKOFF * appr, R), (p, R)]


APPROACH_KW = {"ignore_fingers": True}     # approach legs to a handle / panel: the hand body counts


def _approach_clear(rig, n_free=2):
    """find_park check: the first ``n_free`` legs (the approach, before the hand touches the
    part) collision-free with the hand body counted, not only the arm."""
    kin = rig.kin

    def check(x, y, yaw, qs):
        kw, kin.coll_kw = kin.coll_kw, APPROACH_KW
        try:
            return all(kin.free(q) for q in qs[:n_free]) and \
                all(kin.segment_free(qa, qb) for qa, qb in zip(qs[:n_free - 1], qs[1:n_free]))
        finally:
            kin.coll_kw = kw
    return check


def open_articulated(rig, name, goal=None):
    """Open ``name`` to ``goal`` (default its open value) by its handle: the motion-layer skill "open"
    (skill_jobs.door, skill_plans.plan_door: one grasp, the base riding the part), with the empty hand
    (the right where both are; the body kept while the other holds something, docs 9.3 step 6b).  And
    a microwave by its door key (press_button, step 8b).  A part at its
    goal already is left as it is."""
    a = rig.ann.art(name)
    goal = a["open_q"] if goal is None else goal
    if a["category"] == "microwave":
        # its door moves by its key (press_door, step 8b): pressed with the door to go to goal
        return press_button(rig, f"{name}/door_button", door="open")
    q = rig.joint(name)
    if abs(q - goal) <= (RIDE_DONE_REV if a["type"] == "revolute" else RIDE_DONE_PRIS):
        rig.log("open_result", name=name, before=q, after=q, goal=goal, path="already open")
        return q
    from .motion_skills import SKILLS, run_skill
    return run_skill(rig, SKILLS["open"], {"name": name, "goal": goal})


def close_articulated(rig, name):
    """Close ``name``: the motion-layer skill "close" (skill_jobs.door.close_job: every empty hand x {push
    the door's outer face shut (skill_plans.plan_push), ride its handle shut (plan_door, the right
    hand)} in one park search, docs 9.3 step 6b).  A microwave, or a part with no handle, still the old
    by its door key (press_button, step 8b).  A part closed already is left as it is."""
    a = rig.ann.art(name)
    goal = a["closed_q"]
    if a["category"] == "microwave":
        return press_button(rig, f"{name}/door_button", door="close")
    if a.get("handle") is None:
        raise SkillFailure(f"close {name}: no handle annotated")
    q = rig.joint(name)
    if abs(q - goal) <= (RIDE_DONE_REV if a["type"] == "revolute" else RIDE_DONE_PRIS):
        rig.log("close_result", name=name, before=q, after=q, goal=goal, path="already closed")
        return q
    from .motion_skills import SKILLS, run_skill
    return run_skill(rig, SKILLS["close"], {"name": name})


# ---------------------------------------------------------------- geometry
def _yaw(quat):
    R = quat_R(quat)
    return math.atan2(R[1, 0], R[0, 0])


def _half_along(size, yaw, n):
    """Half extent of a flat box (size, yaw) along the horizontal unit vector n."""
    ex = np.array([math.cos(yaw), math.sin(yaw)])
    ey = np.array([-math.sin(yaw), math.cos(yaw)])
    return abs(float(n @ ex)) * size[0] / 2 + abs(float(n @ ey)) * size[1] / 2


def _perp(n):
    return np.array([-n[1], n[0]])


def _edge_coord(s, n):
    """Coordinate of the support edge with outward normal n (axis aligned), along n."""
    x0, y0, x1, y1 = s["aabb_xy"]
    return {(1, 0): x1, (-1, 0): -x0, (0, 1): y1, (0, -1): -y0}[(int(round(n[0])), int(round(n[1])))]


def _holder_mask(B, s):
    """Obstacle boxes that carry the support itself (table, bookcase...)."""
    x0, y0, x1, y1 = s["aabb_xy"]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return (B[:, 0] <= cx) & (B[:, 3] >= cx) & (B[:, 1] <= cy) & (B[:, 4] >= cy) & \
        (B[:, 2] <= s["z"] - 0.005) & (B[:, 5] >= s["z"] - 0.03)


def _free_beyond(rig, s, n, depth=0.25):
    """No wall/furniture in a slab just beyond the support edge (the
    support's own furniture excluded)."""
    B = rig.world.B[:-1]
    B = B[~_holder_mask(B, s)]
    x0, y0, x1, y1 = s["aabb_xy"]
    # lateral inset: a surface against a wall overlaps the wall box by ~2 cm
    ins = 0.03
    x0, x1 = (x0 + ins, x1 - ins) if x1 - x0 > 3 * ins else (x0, x1)
    y0, y1 = (y0 + ins, y1 - ins) if y1 - y0 > 3 * ins else (y0, y1)
    e = _edge_coord(s, n)
    if abs(n[0]) > 0.5:
        lo = np.array([e + 0.005 if n[0] > 0 else -e - depth, y0, s["z"] - 0.08])
        hi = np.array([e + depth if n[0] > 0 else -e - 0.005, y1, s["z"] + 0.12])
    else:
        lo = np.array([x0, e + 0.005 if n[1] > 0 else -e - depth, s["z"] - 0.08])
        hi = np.array([x1, e + depth if n[1] > 0 else -e - 0.005, s["z"] + 0.12])
    hit = (B[:, 0] < hi[0]) & (B[:, 3] > lo[0]) & (B[:, 1] < hi[1]) & (B[:, 4] > lo[1]) & \
        (B[:, 2] < hi[2]) & (B[:, 5] > lo[2])
    return not bool(hit.any())


def _open_edges(rig, s):
    """Edges of a support a flat object can hang over.  Interior shelves
    (another level above) only open at the front: the side of the depth axis
    with more free space."""
    dirs = [np.array(d, float) for d in ((1, 0), (-1, 0), (0, 1), (0, -1))]
    B = rig.world.B[:-1]
    hold = B[_holder_mask(B, s)]
    if not _interior(rig, s):
        return [n for n in dirs if _free_beyond(rig, s, n)]
    x0, y0, x1, y1 = s["aabb_xy"]
    axis = 0 if (x1 - x0) < (y1 - y0) else 1          # depth axis = the short one
    best, room = None, -1.0
    for sign in (1.0, -1.0):
        n = np.zeros(2)
        n[axis] = sign
        free = 0.0
        for d in np.arange(0.1, 1.01, 0.1):
            if not _free_beyond_hold(rig, s, n, hold, d):
                break
            free = d
        if free > room:
            best, room = n, free
    return [best] if room >= 0.3 else []


def _interior(rig, s):
    """An interior shelf: its holder rises more than 12 cm above it (another level above)."""
    B = rig.world.B[:-1]
    hold = B[_holder_mask(B, s)]
    return bool(len(hold) and float(hold[:, 5].max()) > s["z"] + 0.12)


def _free_beyond_hold(rig, s, n, hold, depth):
    """Slab beyond the holder's own face (for the front of a bookcase)."""
    B = rig.world.B[:-1]
    x0, y0, x1, y1 = s["aabb_xy"]
    lo, hi = np.array([x0, y0, 0.05]), np.array([x1, y1, 1.0])
    k = 0 if abs(n[0]) > 0.5 else 1
    if n[k] > 0:
        face = float(hold[:, 3 + k].max())
        lo[k], hi[k] = face + 0.01, face + depth
    else:
        face = float(hold[:, k].min())
        lo[k], hi[k] = face - depth, face - 0.01
    hit = (B[:, 0] < hi[0]) & (B[:, 3] > lo[0]) & (B[:, 1] < hi[1]) & (B[:, 4] > lo[1]) & \
        (B[:, 2] < hi[2]) & (B[:, 5] > lo[2])
    return not bool(hit.any())


def _overlaps_objects(rig, box, exclude, st, margin=0.02):
    """Whether an object (not in ``exclude``) stands in ``box`` [x0, y0, x1, y1, z0, z1]: its footprint
    (grown by ``margin``) over the box's, its lowest point as it lies (geo.resting) at the box's level.
    Not its box's bottom face: on a round object lying on another face that is up at its middle (11-14,
    T11: an apple 99 deg over in a tray read 3 cm above the tray's floor, and the orange went onto it)."""
    for other in rig.ann.objects:
        if other in exclude:
            continue
        low = float(rig.geo.resting(other, st)[2])
        fp = rig.geo.footprint(other, st, margin)
        if box[0] < fp[2] and fp[0] < box[2] and box[1] < fp[3] and fp[1] < box[3] and \
                box[4] > low - 0.01 and box[5] < low + 0.5:
            return True
    return False


# ---------------------------------------------------------------- pick
def _grasp_approach(g):
    """(u, L): a pinch closes in along the gripper axis u, the last L straight: one finger length and
    LEAVE_MARGIN (pick_approach).  At the grasp only the fingers reach into what the hand closes on
    (between a mug's walls, around a toy car's sides), along the gripper axis, so backed out by a
    finger length they are out of it and the free motion before the line ends in the open.  At the
    4 cm it used to be the fingertips stayed 2 cm inside a mug's rim (a rim pinch 3.5 cm deep): the
    free leg had to bring the open hand round the rim, the planner found that once in nine tries,
    and the park search took the one (P11, T04 no_cup kitchen mug, 2026-11-06)."""
    return -g["R"][:, 2], pick_approach()


def pick_approach():
    """m of a pinch's straight approach: the planner's finger length (finger_model_length) and LEAVE_MARGIN."""
    return finger_model_length() + LEAVE_MARGIN


def _pinch_candidates(rig, obj, pos, quat, kinds, surface_z):
    """The annotated pinches of ``obj`` at (pos, quat), and after them a square block's pinches
    across its other pair of faces; each with ``idx``, its place in that list (the same candidate
    at another pose of the object), a top pinch's TCP raised so its pads clear ``surface_z``."""
    cands = rig.ann.grasp_poses(obj, pos, quat, kinds=kinds)
    extra = []
    if "top_pinch" in kinds and hasattr(rig.ann, "asset_of"):
        extra = [c for c in rig.ann.grasp_poses(obj, pos, quat, kinds=("top_pinch",), extra_rotations=True)
                 if not any(np.allclose(c["R"], c0["R"], atol=1e-3) and np.allclose(c["p"], c0["p"], atol=1e-3)
                            for c0 in cands)]
    for i, c in enumerate(cands + extra):
        c["idx"] = i
        if c["kind"] == "top_pinch":
            c["p"] = _pads_clear_of(c, surface_z)
    return cands, extra


def _surface_under(rig, name, st):
    """The surface a pinch's pads must clear under ``name``: the annotated support it rests on, or
    the lowest point of its box where that is higher (a container's floor).  Not the box's bottom
    face: a curved spoon's box hangs 4.7 mm below the island it lies on, and pads 2 mm above that
    face went into the island.  With no annotated support (the floor) the highest static collider
    under it below its centre, where that is above its box's lowest point: T12's toy car on a rug,
    its box 3.6 mm into the rug's collider, was pinched with the fingers in the rug (Motion.static_top)."""
    o = st["objects"][name]
    size = np.asarray(rig.ann.asset_of(rig.ann.objects[name])["size"], float)
    c = rig.geo.centre(name, st)
    low = float(c[2] - 0.5 * np.abs(quat_R(o["quat"])[2, :]) @ size)
    sup = rig.geo.support_under(name, st)
    if sup is not None:
        return max(low, float(sup["z"]))
    motion = getattr(rig.kin, "motion", None)
    top = None
    if motion is not None and hasattr(motion, "static_top"):
        fp = rig.geo.footprint(name, st)
        top = motion.static_top(fp[:2], fp[2:], float(c[2]))
    return low if top is None else max(low, top)


def _pads_clear_of(g, floor_z, gap=PAD_FLOOR_GAP):
    """A top pinch's TCP raised, where needed, so the lowest corner of its open fingers as the
    planner has them (finger_model_box: the spheres' box, which holds the pad box; opened to
    g["pre_open"] per finger, in the pinch's orientation: a tilted one dips a corner) stays
    ``gap`` (PAD_FLOOR_GAP) above the surface at floor_z (_surface_under; a push: SLIDE_PAD_GAP)."""
    w = float(g["pre_open"])
    half_w, y_in, y_out, tip = finger_model_box()
    corners = np.array([[sx * half_w, sy * (w + t), -tip]
                        for sx in (-1, 1) for sy in (-1, 1) for t in (y_in, y_out)])
    low = float((corners @ np.asarray(g["R"], float).T)[:, 2].min())
    p = np.asarray(g["p"], float).copy()
    p[2] = max(p[2], floor_z + gap - low)
    return p


def _watching(rig, name):
    """rig.clear.watch(name), nothing in minimal rig stubs."""
    clear = getattr(rig, "clear", None)
    return clear.watch(name) if clear is not None and hasattr(clear, "watch") else nullcontext()


def pick(rig, name, max_candidates=12, grasp=None):
    """Pinch grasp from the asset's annotation, one flow for every kind (top, side, rim, thickness):
    a flat object wider than the gripper is pinched across its thickness at a side that overhangs
    its support -- sliding it there is expose's job, not pick's.  (The edge pinch's own flow, the
    push inside pick and the floor corner pinch are gone, 2026-11-05.)

    ``grasp`` "top" / "side" (GRASP_REQUEST) keeps only that pinch kind -- the caller knows where the
    object goes next: a top pinch leaves the palm above the object, too high for a low shelf
    (docs/skills/place.md).  An object without one fails; it never falls back to another kind."""
    obj = rig.ann.objects[name]
    grasps = rig.ann.asset_of(obj)["grasps"]
    if not grasps:
        raise SkillFailure(f"pick {name}: asset '{obj['asset']}' has no Zeno-feasible grasp annotation")
    kinds = GRASP_REQUEST.get(grasp, PINCH_KINDS)
    if not any(g["type"] in kinds for g in grasps):
        raise SkillFailure(f"pick {name}: no {grasp + ' ' if grasp else ''}pinch annotated "
                           f"(has {sorted({g['type'] for g in grasps})})")
    return _pick_pinch(rig, name, max_candidates, kinds)


PINCH_KINDS = ("top_pinch", "side_pinch", "rim_pinch", "rim_pinch_rect", "thickness_pinch")
GRASP_REQUEST = {"top": ("top_pinch",), "side": ("side_pinch",)}   # pick(grasp=...): the kinds it keeps


def _pick_pinch(rig, name, max_candidates=12, kinds=PINCH_KINDS):
    """Pinch pick over the whole waist range, the neighbours in the collision model as they are.
    (The waist used to be capped at 0.2 rad above table height -- a 40-degree bow at a counter
    drove the forearm into an object the arm model then lacked -- and the cap lifted, then the
    neighbour boxes dropped, when no grasp was reachable: 7 and 2 times in the 11-04 full run.
    The arm, its fingers and every object are in the planner's world now.)"""
    return _pick_pinch_core(rig, name, max_candidates, kinds)


class ContactUnreachable(SkillFailure):
    """A contact motion (push, drag, sweep) found no base pose before moving anything."""


def _contact_boxes(rig, name, st, radius=0.40):
    """Loose objects near ``name`` a contact motion on it must keep the hand and fingers out of
    (a push started behind a block came down into the bowl beside it and lifted the bowl).
    Not the object itself, what is held, its contents and lid, nor what it stands on or in."""
    from .predicates import lid_on
    c = rig.geo.centre(name, st)
    z0 = float(rig.geo.bottom(name, st)[2])
    a = rig.ann.asset_of(rig.ann.objects[name])
    held = {h["name"] for h in (rig.held, getattr(rig, "left_held", None)) if h is not None}
    out = []
    for o in rig.ann.objects:
        if o == name or o in held or o not in st["objects"]:
            continue
        if a.get("container") and (rig.geo.inside(o, name, st)[0] or lid_on(rig, name, o, st)[0]):
            continue
        fp = rig.geo.footprint(o, st)
        if math.hypot(max(fp[0] - c[0], 0, c[0] - fp[2]), max(fp[1] - c[1], 0, c[1] - fp[3])) > radius:
            continue
        b = float(rig.geo.bottom(o, st)[2])
        top = b + float(rig.ann.asset_of(rig.ann.objects[o])["size"][2])
        if top < z0 + 0.005 or rig.geo.inside(name, o, st)[0]:
            continue                     # under it (a tray, a mat) or around it (its container)
        out.append([fp[0] - 0.005, fp[1] - 0.005, b, fp[2] + 0.005, fp[3] + 0.005, top + 0.005])
    return out


@contextmanager
def contact_obstacles(rig, name, label):
    """The loose objects near ``name`` as arm and finger obstacles (_contact_boxes) for planning
    a contact motion on it; nothing in minimal rig stubs."""
    world = getattr(rig, "world", None)
    if world is None or not hasattr(world, "temp_obstacles"):
        yield []
        return
    boxes = _contact_boxes(rig, name, rig.state())
    if boxes:
        rig.log("contact_obstacles", obj=name, motion=label, n=len(boxes))
    with world.temp_obstacles(boxes, fingers=True):
        yield boxes


def _pick_pinch_core(rig, name, max_candidates=12, kinds=PINCH_KINDS):
    """The pinch pick of ``name`` (motion_skills.run_skill of pick_job)."""
    from .motion_skills import SKILLS, run_skill
    return run_skill(rig, SKILLS["pick"], {"name": name, "max_candidates": max_candidates, "kinds": kinds})


def _pick_judged(rig, name, g, tcp0, pos, side="right"):
    """Did the pick bring ``name`` along to the carry pose (``side``'s hand at tcp0 when it closed, the
    object at pos before)?  SkillFailure, the hand opened, when not."""
    from .rig import _chain_q, _fingers_of
    after, _ = rig.obj_pose(name)
    tcp, _ = (rig.kin if side == "right" else rig.left_kin).tcp(_chain_q(rig, side))
    rise, lift = float(tcp[2] - tcp0[2]), float(after[2] - pos[2])
    f = _fingers_of(rig, side)
    # it came along: the fingers not shut, and a sticky-hands weld holds it (as check_held has it)
    # or the object up with the hand (a carry pose kept where the arm stood checks the contact
    # exit's few cm).  A weld alone is not held: it carries what slid out of the pads (fingers
    # [0, 0], T13 no_cup mug, T09 spoon), and `holding` judges the fingers
    held = bool(f.min() > SHUT) and (welded(rig, side, name) or rise < PICK_RISE_MIN or lift > PICK_LIFT_FRAC * rise)
    rig.log("pick_result", obj=name, kind=g["kind"], hand=side, lift_m=round(lift, 4), hand_rise_m=round(rise, 4),
            fingers=f.round(4).tolist(), held=held)
    rig.focus_z = None
    if not held:
        setattr(rig, "held" if side == "right" else "left_held", None)   # opened by the failure exit (clearing)
        raise clearing(SkillFailure(f"pick {name}: not held (lift {lift:.3f} m, hand {rise:.3f} m)"), 0.04,
                       leave=False, side=side)
    return True


def _lowest_z(rig, name, st):
    """Lowest corner of the object's box (tilted objects)."""
    o = st["objects"][name]
    a = rig.ann.asset_of(rig.ann.objects[name])
    R = quat_R(o["quat"])
    lo = np.asarray(a["origin_to_bottom_center"], float) - np.r_[np.asarray(a["size"][:2]) / 2, 0.0]
    corners = np.array([[lo[0] + i * a["size"][0], lo[1] + j * a["size"][1], lo[2] + k * a["size"][2]]
                        for i in (0, 1) for j in (0, 1) for k in (0, 1)])
    return float((np.asarray(o["pos"]) + corners @ R.T)[:, 2].min())


def edge_held(rig, name, tcp, R):
    """``rig.held`` fields of a flat object pinched across its thickness at a side (the gripper axis
    along -n, n the side's outward normal): kind "edge", the object's half length along n ``h``, the
    TCP's ``depth`` inside the side, the half width across ``lat_half`` and the TCP's height ``dz``
    above the object's bottom -- what the edge place lays it down by (skill_jobs.place._edge_goals)."""
    st = rig.state()
    _, quat = rig.obj_pose(name)
    size = rig.ann.asset_of(rig.ann.objects[name])["size"]
    n = np.asarray(R, float)[:2, 2]
    n = n / max(1e-9, float(np.linalg.norm(n)))
    b = np.asarray(rig.geo.bottom(name, st), float)
    h = _half_along(size, _yaw(quat), n)
    return {"kind": "edge", "h": h, "depth": float(h - n @ (np.asarray(tcp, float)[:2] - b[:2])),
            "lat_half": _half_along(size, _yaw(quat), _perp(n)), "dz": float(tcp[2] - b[2])}


# ---------------------------------------------------------------- place
PLACE_YAWS = (0, 90, -90, 45, -45, 135, -135, 180)   # deg: wrist turns about the vertical for a place
PLACE_YAW_COST = 0.05         # m of park cost per 45 deg of wrist turn
PLACE_SPOT_COST = 0.05        # ... per rank of the free spot (free_spots order)
PLACE_TILTED_COST = 0.10      # ... for putting the object down as tilted as it hangs (not levelled)


@contextmanager
def fingers_checked(rig):
    """A free-space leg to a pose above a target (drop, hover) as Rig's free space (Rig._fingers_checked):
    the fingers in the arm's collision model -- left out (ignore_fingers), an approach planned low
    from the side swept the open fingers through a tray and the blocks in it -- and no target
    exempted.  Steps 4-5 drop ignore_fingers."""
    with rig._fingers_checked(rig.kin):
        yield


def _carrying(rig, name):
    """Park-search queries with ``name`` in the hand as it is held now (Motion.carrying: the
    relation taken here, at the real base), or nothing to do without cuRobo."""
    motion = rig.kin.motion
    if motion is None or not motion.by_owner.get(f"object:{name}") or \
            (rig.held is not None and rig.held.get("kind") == "bimanual"):
        return nullcontext()           # (a two-hand hold is in neither arm's model: Motion._attach_held)
    rig.sync_world()
    return motion.carrying(rig.kin.side, name, motion.held_in_tcp(rig.kin, rig.q_cmd, name))


def _is_tray(rig, name):
    """A container the place sets things down in as on a support (its floor), not drops them
    into: asset tag "tray" (the serving and sorting trays)."""
    return "tray" in rig.ann.asset_of(rig.ann.objects[name]).get("tags", [])


def _tray_support(rig, tray):
    """The floor of ``tray`` as a support: the top of its base plate (CONTAINER_BASE_T above its
    bottom), inside its walls (CONTAINER_WALL)."""
    st = rig.state()
    b = rig.geo.bottom(tray, st)
    fp = rig.geo.footprint(tray, st)
    return {"name": f"in:{tray}", "furniture": None, "category": "tray", "z": float(b[2]) + CONTAINER_BASE_T,
            "aabb_xy": [fp[0] + CONTAINER_WALL, fp[1] + CONTAINER_WALL, fp[2] - CONTAINER_WALL, fp[3] - CONTAINER_WALL]}


def place(rig, name, support, xy=None, spots=None, square=False):
    """Set the held object down: pick run backwards (docs/motion/COLLISION_PLAN.md 6.2, skills/place.md).
    ``support``: a support surface (at xy, or at any of ``spots``, free_spots order), or
    "in:<container>": a tray's floor the same way, any other container a drop (drop_into).

        carry pose --planned--> set-down start --set-down, straight down--> set-down pose
          --open--> pull-out, straight back along the gripper axis --planned--> travel posture

    One relay pose, the set-down pose: the load's lowest point LEAVE_GAP above the support.  The
    set-down is pick's lift reversed (skill_plans.set_down_length), the pull-out pick's reach-in reversed
    (pick_approach() long); both are checked straight lines, nothing on the way may be touched.  Either hand's
    load (HAND_PLAN 9c)."""
    side = _hand_of(rig, name)
    if side is None:
        raise SkillFailure(f"place {name}: not holding it")
    held = rig.held if side == "right" else rig.left_held
    if support.startswith("in:"):
        container = support[3:]
        if not _is_tray(rig, container):
            return drop_into(rig, name, container)
        # free spots on its floor, the centre first when it is free: with only the centre a second
        # load was set down onto the first (T11 fruit_plate_for_guests, 11-14: the orange 57 mm into
        # the apple at every one of 60 builds)
        floor = _tray_support(rig, container)
        c = rig.geo.centre(container, rig.state())
        spots = free_spots(rig, name, floor, hint=(float(c[0]), float(c[1])), exclude={container})
        rig.log("place_tray_spots", obj=name, tray=container, floor=[round(v, 3) for v in floor["aabb_xy"]],
                spots=[[round(x, 3), round(y, 3)] for x, y in spots[:4]])
        if not spots:
            raise SkillFailure(f"place {name}: no free spot in {container}")
        return _set_down(rig, name, floor, spots[:4], tray=container)
    s = rig.ann.support(support)
    if held["kind"] == "edge":
        # set down over an open edge (skill_jobs.place._edge_goals; xy, if given, ranks the positions), the
        # fingers clear of the support; then pushed on with the catalog's push until its gripped face is
        # EDGE_PUSH_IN inside the edge (place_flat's final push, now checked) -- or, given xy further in,
        # until its centre is there along the edge's normal (a tray hinted on a burner: 1.4 cm short of the
        # old push's spot was off the burner disc, T07 11-15)
        from .skill_jobs.place import EDGE_PUSH_IN
        from .skill_jobs.slide import push_object
        hint = None if xy is None else (float(xy[0]), float(xy[1]))
        x0, y0, x1, y1 = s["aabb_xy"]
        n, over = _set_down(rig, name, s, [hint or ((x0 + x1) / 2, (y0 + y1) / 2)], hint=hint)["edge"]
        dist = over + EDGE_PUSH_IN
        if hint is not None:
            c = np.asarray(rig.geo.centre(name, rig.state()), float)[:2]
            dist = max(dist, float((c - np.asarray(hint)) @ n))
        push_object(rig, name, s, [(-n, dist, None)], label="EDGE_PUSH_IN")
        return True
    return _set_down(rig, name, s, list(spots) if spots is not None else [xy], square=square)


def _set_down(rig, name, s, spots, tray=None, hint=None, square=False):
    """place onto the support ``s`` (an annotated one, or a tray's floor) at one of ``spots``
    (motion_skills.run_skill of place_job); an edge hold over an edge of it, ``hint`` ranking them."""
    from .motion_skills import SKILLS, run_skill
    return run_skill(rig, SKILLS["place"], {"name": name, "support": s, "spots": spots, "tray": tray, "hint": hint,
                                            "square": bool(square)})


def drop_into(rig, name, container):
    """Let the held object go into ``container`` (any container but a tray: place sets things down
    on a tray's floor): motion_skills.run_skill of drop_job (skill_jobs/drop.py, docs/skills/drop_hover.md)."""
    from .motion_skills import SKILLS, run_skill
    return run_skill(rig, SKILLS["drop"], {"name": name, "container": container})


def hint_spot_free(rig, name, s, hx, hy, st=None, skip=None):
    """Whether free_spots takes the hint (hx, hy) itself, as its first spot: the object's own half-size (not
    any-yaw) inside the support (4 cm in from a counter's open edge) and no other object there.  ``s``: the
    support record; ``skip``: objects not in the way (default: the object itself)."""
    st = st if st is not None else rig.state()
    skip = {name} if skip is None else skip
    size = rig.ann.asset_of(rig.ann.objects[name])["size"]
    x0, y0, x1, y1 = s["aabb_xy"]
    re = 0.5 * max(size[0], size[1]) + 0.002          # the object's own half-size, not any-yaw
    re += 0.04 if s.get("category") == "counter" else 0.0   # (off the counter's open edge)
    return bool(x0 + re <= hx <= x1 - re and y0 + re <= hy <= y1 - re and not _overlaps_objects(
        rig, [hx - re, hy - re, hx + re, hy + re, s["z"] + 0.005, s["z"] + size[2]], skip, st, margin=0.005))


def free_spots(rig, name, support, hint=None, k=8, exclude=()):
    """Collision-free xy on a support for the object's footprint, near the
    hint (or near an open edge, where the arm reaches; behind a door, near its
    opening: the arm reaches in from there), best first.  ``support``: an
    annotated support's name, or a support record (a tray's floor, _tray_support);
    ``exclude``: objects that do not count as in the way (the tray itself)."""
    from .annotations import behind_door, opening
    s = support if isinstance(support, dict) else rig.ann.support(support)
    skip = {name, *exclude}
    door = behind_door(rig.ann, s)
    st = rig.state()
    asset = rig.ann.asset_of(rig.ann.objects[name])
    size = asset["size"]
    r = 0.5 * math.hypot(size[0], size[1]) + 0.015          # any yaw
    if (asset.get("container") or {}).get("shape") == "round" or any(g.get("round") for g in asset.get("grasps", [])):
        r = 0.5 * max(size[0], size[1]) + 0.015            # round: yaw does not matter
    if door is not None:
        # The cavity is narrow. The carried container is held upright, so its
        # actual lateral half-width is more useful than its diagonal radius.
        # (No microwave's own radius any more: its -4 mm moved the bowl off the old insertion's low right wall --
        # a scene's special case; the place's plan checks the walls itself.  Rule audit 11-25.)
        r = 0.5 * max(size[0], size[1]) + 0.008
    tray = s.get("category") == "tray"
    if tray:
        # a tray holds loads side by side: the load's own half-size and a 1 cm gap (with the any-yaw
        # radius and 2 cm a 27 cm tray had no room left beside a fruit at its centre)
        r = 0.5 * max(size[0], size[1]) + 0.005
    x0, y0, x1, y1 = s["aabb_xy"]
    if x1 - x0 < 2 * r or y1 - y0 < 2 * r:
        r = 0.5 * min(size[0], size[1]) + 0.01
    edges = (None if tray else _open_edges(rig, s)) or \
        [np.array(d, float) for d in ((1, 0), (-1, 0), (0, 1), (0, -1))]
    out_dir = None if door is None else opening(door)
    front = None if out_dir is None else max(float(out_dir @ np.array(c)) for c in ((x0, y0), (x0, y1), (x1, y0), (x1, y1)))
    bx, by, _ = rig.base_pose()
    out = []
    if hint is not None:
        # an explicit request is honoured exactly when that point itself is free
        hx, hy = float(hint[0]), float(hint[1])
        if hint_spot_free(rig, name, s, hx, hy, st, skip):
            out.append((-1.0, hx, hy))
    # first keep a finger's clearance to every neighbour (the object stays
    # pickable afterwards), then accept the tight 2 cm margin
    # an explicit hint (swap onto the other's spot, a requested position) is
    # honoured closely: tight margin first; otherwise keep finger clearance first
    # (7 cm first: lowered 4.5 cm from a rolling pin, a rim-held bowl and the
    # hand around it pushed the pin and the bowl came to rest tilted on it)
    first = (0.10,) if asset.get("container") else ()   # the hand wraps a rim-held bowl
    step = 0.015 if tray else 0.03
    for margin in ((0.01,) if tray else
                   (0.02, 0.045) if hint is not None and not s["name"].startswith("breakfast_fridge")
                   else first + (0.07, 0.045, 0.02)):
        # 4 cm in from the open edges of a counter: a block left 3 cm from the
        # island edge was knocked off by the robot body driving along it
        ins = 0.04 if s.get("category") == "counter" else 0.0
        for x in np.arange(x0 + r + ins, x1 - r - ins + 1e-6, step):
            for y in np.arange(y0 + r + ins, y1 - r - ins + 1e-6, step):
                box = [x - r, y - r, x + r, y + r, s["z"] + 0.005, s["z"] + size[2]]
                if _overlaps_objects(rig, box, skip, st, margin=margin):
                    continue
                to_edge = min(_edge_coord(s, n) - float(n @ np.array([x, y])) for n in edges)
                if out_dir is not None:
                    # behind a door: as deep in as the spot stands from the opening (the pick
                    # behind a door takes the most outward grasp first, door_access.outward)
                    to_edge = front - float(out_dir @ np.array([x, y]))
                # no hint: prefer spots near the robot (all edge spots score 0 otherwise
                # and the search started in the far corner of a long counter)
                score = (math.hypot(x - hint[0], y - hint[1]) if hint is not None
                         else 0.3 * math.hypot(x - bx, y - by)) + \
                    (to_edge if out_dir is not None else 0.5 * max(0.0, to_edge - 0.2))
                out.append((score, float(x), float(y)))
        if len(out) > (1 if hint is not None and out and out[0][0] < 0 else 0):
            break
    out.sort()
    return [(x, y) for _, x, y in out[:k]]


def place_on(rig, name, support, hint=None, tries=4, square=False):
    """Place the held object on a support at the best free spot (``square``: squared to the support's axes,
    skill_jobs.place)."""
    held = rig.held if _hand_of(rig, name) == "right" else getattr(rig, "left_held", None)
    if held is not None and held["kind"] == "edge":
        return place(rig, name, support, hint)
    spots = free_spots(rig, name, support, hint)
    if not spots:
        raise SkillFailure(f"place {name}: no free spot on {support}")
    # the free spots are one goal set of the place (not tried one after another)
    return place(rig, name, support, spots=spots[:tries], square=square)


def press_button(rig, button, on=None, door=None):
    """Press the annotated button ``button`` ("<appliance>/<key>") with the closed fingertips of the empty hand:
    run_skill of the catalog's press (skill_jobs.press, skill_plans.plan_press) -- the reach, the press and
    the way back out one plan, from a park whose search checks the press itself.  ``on``: what the press
    switches its appliance's heat source to (None: nothing; the microwave's start key: on).  ``door``
    ("open" / "close", a door key): the press drives the appliance's powered door there too."""
    from .motion_skills import SKILLS, run_skill
    return run_skill(rig, SKILLS["press"], {"button": button, "on": on, "door": door})


def _powered_door(rig, name, verb):
    """Open (``verb`` "open") or close a powered door -- the microwave's -- by its door key: one press whose plan
    ends with the door driven by its motor, from a park clear of its swing (skill_plans.plan_press press_door).
    The empty hand presses (the right where both are).  Already there: nothing moves."""
    a = rig.ann.art(name)
    goal = a["open_q"] if verb == "open" else a["closed_q"]
    q = rig.joint(name)
    if abs(q - goal) <= 0.10:
        return q
    if verb == "open" and abs(q - a["closed_q"]) > 0.10:
        raise SkillFailure(f"microwave: door is neither closed nor open ({q:.3f})")
    press_button(rig, f"{name}/door_button", door=verb)
    return rig.joint(name)


def open_microwave_door(rig, name="kitchen_microwave"):
    """Press the door key: the door's motor opens it (_powered_door)."""
    return _powered_door(rig, name, "open")


def close_microwave_door(rig, name="kitchen_microwave"):
    """Press the door key: the door's motor closes it (_powered_door)."""
    return _powered_door(rig, name, "close")


def cycle_microwave_door(rig, name="kitchen_microwave"):
    """Composite demonstration: open, then close the powered microwave door."""
    a = rig.ann.art(name)
    if abs(rig.joint(name) - a["closed_q"]) > 0.10:
        raise SkillFailure("microwave: door must begin closed for inspection")
    open_microwave_door(rig, name)
    close_microwave_door(rig, name)
    return True
