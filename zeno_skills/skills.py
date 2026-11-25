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
from .planner import find_park, find_park_set, joint_reachable, torque_ratio
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
PLACE_APPROACH = 0.05         # m: wipe's press straight (tooluse); place measures its set-down (skill_plans.set_down_length)


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
            raise clearing(exc, 0.04, leave=False, ticks=20)
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


def held_vertical_move(rig, dz, label, R_goal=None, step=0.005, allow_pull=True):
    """Move the held object up (or down) by dz at the current base.  Straight
    up when the arm allows; otherwise from a staging point pulled toward the
    body (an arm stretched out after a far pick has no vertical range left)."""
    tcp, R = rig.kin.tcp(rig.q_cmd)
    R_goal = R if R_goal is None else R_goal
    x, y, _ = rig.base_pose()
    toward = np.array([x, y]) - tcp[:2]
    dist = float(np.linalg.norm(toward))
    unit = toward / dist if dist > 1e-6 else np.zeros(2)
    last = None
    for pull in ((0.0, 0.08, 0.15, 0.22, 0.30) if allow_pull else (0.0,)):
        pull = min(pull, max(0.0, dist - 0.30))
        goal = tcp + np.r_[unit * pull, dz]
        q_goal, ok = rig.kin.ik_global(goal, R_goal, seeds=[rig.q_cmd])
        # a held load must not ride a big arm reconfiguration (a 12 s swing
        # to another IK branch flung a mug 4 m across the kitchen)
        if not ok or float(np.max(np.abs(np.asarray(q_goal) - rig.q_cmd))) > 1.2:
            continue
        stage = tcp + np.r_[unit * pull, max(0.0, dz) * 0.3]
        if pull > 0:
            q_stage, ok = rig.kin.ik_global(stage, R, seeds=[rig.q_cmd])
            if not ok or float(np.max(np.abs(np.asarray(q_stage) - rig.q_cmd))) > 1.0:
                continue
        try:
            if pull > 0:
                rig.move_to(stage, R, step=step, steps_per_wp=5,
                            label=f"{label}_stage", allow=FREE_ELSE_STRAIGHT, smooth=True, q_hint=q_stage)
                check_held(rig, f"{label}_stage")
            rig.move_to(goal, R_goal, step=step, steps_per_wp=5, label=label, allow=FREE_ELSE_STRAIGHT, smooth=True)
            check_held(rig, label)
            return goal
        except SkillFailure as exc:
            last = exc
            if rig.held is None:
                raise
            tcp, R = rig.kin.tcp(rig.q_cmd)
    raise last or SkillFailure(f"{label}: no IK for a {dz:+.2f} m vertical move from any staging point")


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


def _swing_arm(rig, side, arm_q, label):
    """Move one arm's joints (torso and waist kept) to ``arm_q``: straight in joint space when
    that is clear, else a cuRobo trajectory.  False (logged) when neither exists."""
    kin = rig.kin if side == "right" else rig.left_kin
    start = rig.q_cmd.copy() if side == "right" else np.r_[rig.q_cmd[:2], rig.left_q_cmd]
    goal = np.r_[start[:2], np.asarray(arm_q, float)[2:]]
    if np.max(np.abs(goal - start)) < SAME_POSTURE:
        return True
    rig.clear.motion(label, FREE, side=side)
    if kin.segment_free(start, goal):
        vias = [goal]
    else:
        vias, status = kin.plan(start, goal)
        if vias is None:
            rig.log(f"{label}_blocked", side=side, status=str(status))
            return False
    if side == "right":
        rig.follow(rig.joint_path_via(vias))
    else:
        qs, qa = [], start
        for qb in vias:
            qs += rig._dense(qa, np.asarray(qb, float))
            qa = qb
        rig.left_follow(qs)
    rig.log(label, side=side)
    return True


def _fold_left(rig):
    """An empty left arm left out (a brace, a hold released) folds to its travel posture
    before the base drives: straight when that is clear, else a cuRobo trajectory; when
    neither exists it stays where it is."""
    if rig.left_held is not None:
        return
    rig.sync_world()
    _swing_arm(rig, "left", rig.left_kin.rest, "left_fold")


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


def _ride_check(rig, a, q_from, q_to):
    """Base follows the part rigidly: footprint + arm must stay clear."""
    ann, kin, world = rig.ann, rig.kin, rig.world
    M0inv = np.linalg.inv(ann.motion(a, q_from))

    def check(x, y, yaw_deg, q_arm):
        ok = True
        saved = world.joint_q[a["name"]]
        for q in np.linspace(q_from, q_to, 8)[1:]:
            M = ann.motion(a, q) @ M0inv
            p = M[:3, :3] @ np.array([x, y, 0.0]) + M[:3, 3]
            dyaw = math.atan2(M[1, 0], M[0, 0])
            world.set_joint(a["name"], q)
            if not world.footprint_clear(p[0], p[1], math.radians(yaw_deg) + dyaw):
                ok = False
                break
            kin.set_base((p[0], p[1], 0.0), math.radians(yaw_deg) + dyaw)
            # the arm against the part where it will be then (closing, the robot swings
            # through where the open door is now)
            motion = getattr(kin, "motion", None)
            with motion.part_at(a["name"], q) if motion is not None else nullcontext():
                free = kin.free(q_arm)
            if not free:
                ok = False
                break
        world.set_joint(a["name"], saved)
        kin.set_base((x, y, 0.0), math.radians(yaw_deg))
        return ok
    return check


def _ride(rig, a, goal, lead=0.03, rate=0.25):
    """Closed loop: read the real joint value, put the base at the pose that
    keeps the robot rigid w.r.t. the part at (value + lead).  The grasped
    handle is the only thing that moves the part."""
    ann = rig.ann
    x0, y0, yaw0 = rig.base_pose()
    q_start = rig.joint(a["name"])
    Minv0 = np.linalg.inv(ann.motion(a, q_start))
    sign = 1.0 if goal > q_start else -1.0
    cmd, last, stall = q_start, q_start, 0
    for it in range(6000):
        q = rig.joint(a["name"])
        if sign * (goal - q) <= 0.02 * (1 if a["type"] == "revolute" else 0.3):
            rig.log("ride_done", q=q)
            return True
        target = q + sign * lead if sign * (goal - (q + sign * lead)) > 0 else goal + sign * 0.02
        cmd += float(np.clip(target - cmd, -rate / PHYSICS_HZ, rate / PHYSICS_HZ))
        M = ann.motion(a, cmd) @ Minv0
        p = M[:3, :3] @ np.array([x0, y0, 0.0]) + M[:3, 3]
        rig.set_base(p[0], p[1], yaw0 + math.degrees(math.atan2(M[1, 0], M[0, 0])))
        rig.step(1)
        if it % 60 == 0:
            rig.log("ride", q=round(q, 4), cmd=round(cmd, 4), fingers=[round(v, 4) for v in rig.fingers()])
            if abs(q - last) < 0.003 and it:
                stall += 1
                if stall >= 4:
                    return False
            else:
                stall = 0
            last = q
    return False


def _move_articulated(rig, name, goal, verb):
    a = rig.ann.art(name)
    if a.get("handle") is None:          # e.g. a PartNet microwave without a handle part
        raise SkillFailure(f"{verb} {name}: no graspable handle annotated")
    q0 = rig.joint(name)
    rig.sync_world()
    rig.kin.coll_kw = {"hand_touches_part": True}
    # among feasible parks prefer the one whose arm can pull hardest along the
    # handle's motion (the 3 N·m wrist joints were the weak link)
    pull = np.asarray(a["handle"]["outward"], float) * (1 if goal != a["closed_q"] else -1) * 20.0

    failed = getattr(rig, "_failed_art_parks", {}).get(name, [])

    def score(x, y, yaw, qs):
        if any(math.hypot(x - fx, y - fy) < 0.20 for fx, fy, _ in failed):
            return 1e9                     # a ride from here already left the part unmoved: last resort
                                           # (find_park keeps the lowest score)
        rig.kin.set_base((x, y, 0.0), math.radians(yaw))
        return torque_ratio(rig.kin, qs[-1], pull)
    # doors hook from the free side; a drawer pull from either end
    park = None
    # untilted first; tilted side hooks for bars close to their panel; last a
    # front pinch across the bar (held by friction), for a handle whose free
    # side is blocked (the two middle handles of a double door)
    hooks = [("side", flip, tilt) for tilt in (0.0, math.radians(10), math.radians(20))
             for flip in ((False, True) if a["type"] == "prismatic" or a["handle"].get("flip_ok") else (False,))]
    if a["handle"].get("grasp") == "front":            # round pull: no gap behind it to hook into
        hooks = []
    if a["handle"].get("pre_open") is not None:        # imported handles (bar geometry annotated)
        hooks.append(("front", False, 0.0))
    for grasp, flip, tilt in hooks:
        p, R, appr, targets = _handle_targets(rig, a, q0, flip, tilt, grasp)
        if a["category"] == "microwave" and verb == "open" and abs(q0 - a["closed_q"]) < 0.05:
            # Park beside the hinge sweep. A frontal park can be IK-valid yet
            # the tucked robot grazes the door while navigating to it.
            h = a["handle"]
            side = np.asarray(h["along"], float)
            outward = np.asarray(h["outward"], float)
            xy = np.asarray(h["center"], float)[:2] - 0.555 * side[:2] - 0.25 * outward[:2]
            yaw = math.degrees(math.atan2(outward[1], outward[0])) + 15.0
            park = find_park(rig.kin, rig.world, targets, near=(xy[0], xy[1], yaw),
                             q_start=None, travel_q=_travel_q(rig),
                             ride=_ride_check(rig, a, q0, goal), check=_approach_clear(rig), max_tries=1)
            if park is not None:
                rig.kin.set_base((park[0], park[1], 0.0), math.radians(park[2]))
                if not joint_reachable(rig.kin, _travel_q(rig), park[3][0]):
                    park = None
            if park is not None:
                break
        park = find_park(rig.kin, rig.world, targets, near=rig.base_pose(), q_start=rig.q_cmd, travel_q=_travel_q(rig),
                         ride=_ride_check(rig, a, q0, goal), check=_approach_clear(rig), score=score,
                         n_best=1 if a["category"] == "refrigerator" else 3 if a["category"] == "microwave" else 10)
        if park is not None:
            break
    if park is None:
        raise SkillFailure(f"{verb} {name}: no base pose can grasp the handle and ride the motion")
    x, y, yaw, park_qs = park
    rig._last_art_park = (name, (x, y, yaw))
    rig.log(f"{verb}_park", park=[round(x, 3), round(y, 3), round(yaw, 1)], hook_side="far" if flip else "near",
            tilt_deg=round(math.degrees(tilt)), grasp=grasp)
    rig.caption = f"{verb.upper()} {a['category']}: go to handle"
    _goto_park(rig, park)
    rig.kin.coll_kw = {"hand_touches_part": True}
    q_now = rig.joint(name)
    rig.log(f"{verb}_at_park", q_before=q0, q_now=q_now)
    if abs(q_now - q0) > 0.01:          # the part moved meanwhile: re-plan from here
        q_prev, q0 = q0, q_now
        rig.sync_world()
        p, R, appr, targets = _handle_targets(rig, a, q0, flip, tilt, grasp)
        bx, by, byaw = rig.base_pose()
        if abs(q_now - q_prev) < 0.05 and math.hypot(x - bx, y - by) <= AT_PARK_M:
            # Only a brush of the base nudged it: stay, and solve the handle
            # IK afresh from the real base pose instead of reusing stale hints.
            park_qs = (None, None, None)
        else:
            park = find_park(rig.kin, rig.world, targets, near=rig.base_pose(), q_start=rig.q_cmd,
                             ride=_ride_check(rig, a, q0, goal), check=_approach_clear(rig), score=score, n_best=5)
            if park is None:
                raise SkillFailure(f"{verb} {name}: part moved to {q0:.3f} and no base pose reaches it now")
            _goto_park(rig, park)
            rig.sync_world()
            park_qs = park[3]
    rig.caption = f"{verb.upper()} {a['category']}: grasp handle ({'side hook' if grasp == 'side' else 'front pinch'})"
    # a bar close to its panel (PartNet handles, ~3 cm gap): open only as far as
    # keeps the inner pad between panel and bar
    pre_open = a["handle"].get("pre_open", 0.04)
    t = a["handle"].get("thickness", 0.025)
    if grasp == "front":                  # the fingers straddle the bar across its width
        t = float(np.abs(np.asarray(a["handle"]["bar_size"], float)) @ np.abs(np.asarray(a["handle"]["along"], float)))
        pre_open = min(0.04, t / 2 + 0.015)
    rig.grip(pre_open, 90)        # fingers may start closed (after a push or a knock)
    for (tp, tR), lab, st, qh in zip(targets, ("pre_high", "pre", "handle"), (0.02, 0.01, 0.004), park_qs):
        # the hand body counts until the last leg onto the handle
        rig.kin.coll_kw = {"hand_touches_part": True} if lab == "handle" else APPROACH_KW
        rig.move_to(tp, tR, step=st, steps_per_wp=4 if lab == "handle" else 3, label=f"{verb}_{lab}", q_hint=qh)
    rig.kin.coll_kw = {"hand_touches_part": True}
    f = rig.grip(0.0, PHYSICS_HZ)
    from .skill_jobs.door import handle_closed_on
    if not handle_closed_on(f, t):
        raise SkillFailure(f"{verb} {name}: handle not grasped, fingers {f.round(4).tolist()}")
    rig.caption = f"{verb.upper()} {a['category']}: base follows the joint motion"
    if grasp == "front":                  # held by friction only: pull gently
        _ride(rig, a, goal, lead=0.01, rate=0.12)
    else:
        _ride(rig, a, goal)
    rig.step(30)
    rig.caption = f"{verb.upper()} {a['category']}: release"
    rig.grip(pre_open, 70)
    q = rig.joint(name)
    p, R, appr = rig.ann.handle_pose(a, q, grasp, flip, tilt)
    # the hand is free already: back off as far as the arm allows, then up
    for back in (0.14, 0.08, 0.04):
        try:
            rig.move_to(p - back * appr, R, step=0.006, steps_per_wp=4, label=f"{verb}_back", allow=LEAVE_CONTACT)
            rig.move_to(p - back * appr + np.array([0, 0, 0.12]), R, step=0.01, label=f"{verb}_up",
                        allow=FREE_ELSE_STRAIGHT)
            break
        except SkillFailure as e:
            rig.log("retreat_short", back=back, reason=str(e))
    else:                                 # no straight retreat: at least lift the open hand off the handle
        try:
            rig.move_to(p + np.array([0, 0, 0.08]), R, step=0.005, label=f"{verb}_up", allow=FREE_ELSE_STRAIGHT)
        except SkillFailure as e:
            rig.log("retreat_short", back=0.0, reason=str(e))
    rig.step(60)
    q = rig.joint(name)
    rig.log(f"{verb}_result", name=name, before=q0, after=q, goal=goal)
    if a["type"] == "revolute":
        tol = DOOR_OPEN_TOL
    elif goal == a["closed_q"]:
        tol = DOOR_CLOSED_TOL
    else:                    # a released drawer slides back a little
        tol = DRAWER_OPEN_FRAC * abs(a["open_q"] - a["closed_q"])
    ok = abs(q - goal) < tol
    if not ok:
        raise SkillFailure(f"{verb} {name}: joint {q0:.3f} -> {q:.3f}, goal {goal:.3f}")
    return q


def _move_with_retry(rig, name, goal, verb):
    """Waist kept nearly upright while the left hand carries a load: bending
    it swings the left arm (and its load) into the furniture being worked
    (a 39-degree bow to a cabinet door knocked a rolling pin out)."""
    if getattr(rig, "left_held", None) is None or not hasattr(rig.kin, "names"):
        return _move_with_retry_impl(rig, name, goal, verb)
    widx = rig.kin.names.index("waist_pitch_joint")
    hi = float(rig.kin.hi[widx])
    rig.kin.hi[widx] = min(hi, 0.25)
    try:
        return _move_with_retry_impl(rig, name, goal, verb)
    finally:
        rig.kin.hi[widx] = hi


def _move_with_retry_impl(rig, name, goal, verb):
    """A handle grasp can slide along the bar from some parks (the joint does
    not move at all): remember that park and try once from another."""
    q0 = rig.joint(name)
    try:
        return _move_articulated(rig, name, goal, verb)
    except SkillFailure as exc:
        last = getattr(rig, "_last_art_park", None)
        progress = abs(rig.joint(name) - q0) / max(1e-6, abs(goal - q0))
        if rig.held is not None or last is None or last[0] != name or progress > 0.3 \
                or not ("joint" in str(exc) or "handle not grasped" in str(exc)) \
                or not getattr(rig, "auto_recovery", True):
            raise
        if not hasattr(rig, "_failed_art_parks"):
            rig._failed_art_parks = {}
        rig._failed_art_parks.setdefault(name, []).append(last[1])
        rig.log(f"{verb}_retry_other_park", failed_park=[round(v, 3) for v in last[1]])
        rig.grip(0.04, 40)              # let go of the handle before the arm folds away from it
        rig.tuck()
        return _move_articulated(rig, name, goal, verb)


def open_articulated(rig, name, goal=None):
    """Open ``name`` to ``goal`` (default its open value) by its handle: the motion-layer skill "open"
    (skill_jobs.door, skill_plans.plan_door: one grasp, the base riding the part), with the empty hand
    (the right where both are; the body kept while the other holds something, docs 9.3 step 6b).  Still
    the old _move_with_retry for a microwave (its park beside the hinge sweep: step 8).  A part at its
    goal already is left as it is."""
    a = rig.ann.art(name)
    goal = a["open_q"] if goal is None else goal
    if a["category"] == "microwave":
        return _move_with_retry(rig, name, goal, "open")
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
    _move_with_retry (step 8).  A part closed already is left as it is."""
    a = rig.ann.art(name)
    goal = a["closed_q"]
    if a["category"] == "microwave" or a.get("handle") is None:
        return _move_with_retry(rig, name, goal, "close")
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
                       leave=False)
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


def park_over(rig, label, anchors, off, R, anchor_cost=None, max_tries=150, check=None):
    """A park and TCP goal holding the load with its reference point at one of ``anchors`` (a drop
    above a rim, a hover above a target): those points with the hand turned about the vertical
    through them in PLACE_YAWS steps are one goal set (find_park_set), each checked with the load
    in the hand and the fingers in the collision model, as the motion there is (fingers_checked).
    ``off``: TCP minus the reference point now (world frame), ``R``: the TCP rotation now;
    ``anchor_cost``: m of park cost per anchor; ``check``: find_park's.  (park, p, R_goal) or None."""
    anchors = [np.asarray(a, float) for a in (anchors if np.ndim(anchors) == 2 else [anchors])]
    anchor_cost = [0.0] * len(anchors) if anchor_cost is None else list(anchor_cost)
    goals = [(a + rz(math.radians(d)) @ off, rz(math.radians(d)) @ R, d, i)
             for i, a in enumerate(anchors) for d in PLACE_YAWS]
    rig.sync_world()
    rig.kin.coll_kw = {"ignore_fingers": True}
    with _carrying(rig, rig.held["name"]) if rig.held is not None else nullcontext():
        found = find_park_set(rig.kin, rig.world, [[(p, Rg, FREE_SPACE_KW)] for p, Rg, _, _ in goals],
                              [PLACE_YAW_COST * abs(d) / 45.0 + anchor_cost[i] for _, _, d, i in goals],
                              near=rig.base_pose(), max_tries=max_tries, q_start=rig.q_cmd,
                              travel_q=_travel_q(rig), carry=rig.held is not None, check=check)
    if found is None:
        return None
    park, k = found
    p, Rg, d, i = goals[k]
    rig.log(f"{label}_park", park=[round(v, 3) for v in park[:3]], yaw_deg=d, anchor=i)
    return park, p, Rg


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


def place(rig, name, support, xy=None, spots=None):
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
    return _set_down(rig, name, s, list(spots) if spots is not None else [xy])


def _set_down(rig, name, s, spots, tray=None, hint=None):
    """place onto the support ``s`` (an annotated one, or a tray's floor) at one of ``spots``
    (motion_skills.run_skill of place_job); an edge hold over an edge of it, ``hint`` ranking them."""
    from .motion_skills import SKILLS, run_skill
    return run_skill(rig, SKILLS["place"], {"name": name, "support": s, "spots": spots, "tray": tray, "hint": hint})


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
        r = 0.5 * max(size[0], size[1]) + 0.008
        if s.get("furniture") == "kitchen_microwave":
            # The round bowl can safely overhang the flat floor by a few mm.
            # This shifts it left of the low right wall during insertion.
            r = 0.5 * max(size[0], size[1]) - 0.004
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


def place_on(rig, name, support, hint=None, tries=4):
    """Place the held object on a support at the best free spot."""
    held = rig.held if _hand_of(rig, name) == "right" else getattr(rig, "left_held", None)
    if held is not None and held["kind"] == "edge":
        return place(rig, name, support, hint)
    spots = free_spots(rig, name, support, hint)
    if not spots:
        raise SkillFailure(f"place {name}: no free spot on {support}")
    # the free spots are one goal set of the place (not tried one after another)
    return place(rig, name, support, spots=spots[:tries])


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
