"""Contact skills (docs/motion/MOTION_ARCHITECTURE.md section 6, contact): an object pushed or dragged across its
support by the closed fingers -- plan_slide; a held spoon stirred round inside a pot -- plan_stir; an appliance's
button pressed by the closed fingertips -- plan_press.  Its trajectory is a task segment over the hand's travel
(primitives.Pushed: the object along n from where the fingers meet it, the hand rigid in its frame), checked
whole with the object where each step of the push puts it, as far as the arm reaches from the park; where
the object really went is read at the anchor after it."""

from __future__ import annotations

import time

import numpy as np

from ..clearance import LEAVE_CONTACT, Allow
from ..motion_state import Aim, Failure, Plan, Segment, Spec, aim_pose, decisions_of, with_arm, with_part, with_width
from ..primitives import JointSet, Script, free_at, free_leg, pushed, query, scripted, sided, still, straight
from ..tolerances import SLIDE_TOL, STIR_TOL, WIPE_TOL
from ._common import FREE_HAND, built_so_far, _aimed, _contact, _kept, _move, _reach, anchor, may_touch

SLIDE_STAGES = ("slide_arrive", "slide_close_hand", "slide_reach", "slide_down", "slide_in", "slide_push",
                "slide_moved", "slide_leave", "tuck", "slide_open_hand")
SLIDE_ANCHORS = ("slide_arrive", "slide_moved")   # the base and the object; where the push left it
SLIDE_RELAY = "slide_end"     # what the park search's ranking IK solves (park_search.Problem.relay): the push's
                              # end -- or, where no park reaches all of it, the farthest along it a park's arm
                              # gets (Problem.relay_from); the descent's start alone ranked parks from which 14 of
                              # 15 pushes ran out of IK along the way (T05 notebook 11-12).  A seed, not a
                              # decision: its solution seeds slide_reach's IK (decide_ik's first seed) on that branch
SLIDE_OPEN = 0.04             # m per finger the hand is left open at the end (skills' old push: for what comes next)
SLIDE_STEP = 0.02             # m of travel between the push's checked samples (docs 2.4: by travel; not measured)


def slide_travel(plan):
    """m a plan's push moves its object -- the hand's travel less its lag: the plan's prediction -- or
    None (no push in it)."""
    seg = next((sg for sg in getattr(plan, "segments", ()) if sg.name == "slide_push"), None)
    if seg is None:
        return None
    sc = seg.info["script"]
    return sc.coupling.travel(sc.s1)


def plan_slide(kin, state, push, rest_goals, start="slide_arrive", prior=None, step=0.003):
    """The object push["obj"] pushed along the horizontal unit push["n"] by ``kin``'s closed hand from
    ``state``, as far as the arm reaches from here: push = {obj, T_obj_tcp (the push point: the TCP in
    the object's box frame where the push starts), n, d (m the hand runs along n at most), lag (m it runs
    before the object moves: primitives.Pushed), least (m the object must move on this leg: less fails
    the plan), above (m: the hand comes straight down from this far above where it lands), back (m: it
    lands this far behind the push point along -n, the push-in closes it; 0: on it -- a drag pressing on
    the top)}:

        slide_arrive      anchor: the base and the object as they are
        slide_close_hand  close the fingers: one blunt tip
        slide_reach       the free leg to ``above`` over where the descent lands (decide_ik: _reach)
        slide_down        the straight down
        slide_in          the straight along n onto the push point (none when back is 0)
        slide_push        the task segment (Script, primitives.Pushed, carry "arm"): the hand along n as
                          far as the arm has IK, up to push["d"] (scripted's reach: the leg is measured,
                          not set), the object moving from s = lag on; the fingers may touch it
        slide_moved       anchor: where the object went
        slide_leave       out of the contact: the straight away from what the fingers touch -- up and off
                          the pushed face at 45 deg (a drag: up off the top) -- as far as contact_extent
                          measures (near_world: LEAVE_GAP clear, then LEAVE_MARGIN); none when nothing is
                          touched
        tuck              the first free of ``rest_goals`` (JointSet; never kept)
        slide_open_hand   the hand opened for what comes next

    The reach, the descent and the push-in carry the Aim (the push point in the object's frame) and
    SLIDE_TOL (primitives.holds checks them again).  From ``start`` on; ``prior`` as plan_pick's (a
    Plan: its motions that still hold kept, its decisions tried first; else the park search's ranking
    solution of the push's end, SLIDE_RELAY) -- slide_reach, the descent's start.  Plan or Failure."""
    with query(kin, state, FREE_HAND):          # kin.tcp at the state's base throughout
        return _plan_slide(kin, state, push, rest_goals, start, prior, step)


def _plan_slide(kin, state, push, rest_goals, start, prior_plan, step):
    i0 = SLIDE_STAGES.index(start)
    prior = decisions_of(prior_plan)
    obj, side = push["obj"], kin.side
    n = np.asarray(push["n"], float)
    up = np.array([0.0, 0.0, 1.0])
    back, above = float(push["back"]), float(push["above"])
    aim = Aim(obj, np.asarray(push["T_obj_tcp"], float), side=side)
    aimed = aim_pose(state, aim)
    if aimed is None and i0 <= SLIDE_STAGES.index("slide_push"):
        return Failure(f"{obj} is not in the State", start)
    p, R = aimed if aimed is not None else (None, None)
    land = None if p is None else p - back * n                     # where the descent lands
    on_it = may_touch(side, obj, "the closed fingers onto the object they push")
    # out of the contact: away from both things the fingers touch -- the pushed face (-n) and the support
    # (up) -- or off a drag's top
    out = up - n if back > 0 else up
    out = out / np.linalg.norm(out)
    q, s = state.q(side), state
    segs, decided, times = [], {}, {}
    for stage in SLIDE_STAGES[i0:]:
        t0 = time.time()
        kept = _kept(kin, s, q, prior_plan, stage) if stage != "tuck" else None
        if stage in SLIDE_ANCHORS:
            seg = anchor(stage, q, s, (obj,), side)
        elif stage == "slide_close_hand":
            # a second, as pick's close (run: PHYSICS_HZ ticks): 30 ticks left the fingers ~2 cm open each, and the
            # next segment, built with them closed, was checked with them open (T27 rice, the left hand, 11-25)
            seg = Segment(stage, FREE_HAND, q, kind="action", action=("grip", 0.0, None, False))
            s = with_width(s, side, 0.0)
        elif stage == "slide_reach":
            seg = kept or _reach(kin, s, FREE_HAND, land, R, -up, above, q, prior.get(stage, prior.get(SLIDE_RELAY)),
                                 stage, step)
            if not isinstance(seg, Failure):
                seg = kept or _aimed(kin, seg, aim, aimed, SLIDE_TOL, steps_per_wp=3)
                if seg.qs:                                  # the descent's start as the plan reaches it
                    decided[stage] = seg.q_end
        elif stage == "slide_down":
            spec = FREE_HAND if back > 0 else on_it        # a drag lands on the object, a push behind it
            seg = kept or straight(kin, s, spec, land, R, stage, step=step, q_from=q)
            if not (isinstance(seg, Failure) or kept):
                seg = _aimed(kin, seg, aim, aimed, SLIDE_TOL, steps_per_wp=4)
        elif stage == "slide_in":
            if back <= 0:
                continue
            seg = kept or straight(kin, s, on_it, p, R, stage, step=step, q_from=q)
            if not (isinstance(seg, Failure) or kept):
                seg = _aimed(kin, seg, aim, aimed, SLIDE_TOL, steps_per_wp=4)
        elif stage == "slide_push":
            T0 = s.objects.get(obj)
            if T0 is None:
                return Failure(f"{obj} is not in the State", stage, {"stage_s": times})
            script = Script(pushed(obj, T0, n, push["lag"]), 0.0, float(push["d"]), step=SLIDE_STEP, carry="arm")
            # from the arm as the plan has it (q: on the push point), not as the State it moves on had it;
            # kept as it is while it holds (_kept: the IK continuation made again comes out a little
            # otherwise, and what follows from its end with it)
            seg = kept or scripted(kin, with_arm(s, q, side), on_it, script, stage, arm_step=step, reach=True)
            if not (isinstance(seg, Failure) or kept):
                seg = _move(seg, steps_per_wp=4)
            if not isinstance(seg, Failure):
                sc = seg.info["script"]             # the one it runs (a kept one's own), ending where the arm got
                gone = sc.coupling.travel(sc.s1)
                if gone < float(push["least"]):
                    seg = Failure(f"the arm pushes {obj} only {gone:.3f} m from here (the hand to s={sc.s1:.3f}, "
                                  f"{float(push['least']):.3f} m asked at least)", stage)
                else:
                    s = sc.coupling.moved(s, sc.s1)
        elif stage == "slide_leave":
            seg = kept or _contact(kin, s, Spec(allow=LEAVE_CONTACT), out, "near_world", stage, step, q,
                                   steps_per_wp=3, smooth=True)
            if not isinstance(seg, Failure) and not seg.qs:    # touching nothing: no exit
                times[stage] = round(time.time() - t0, 3)
                continue
        elif stage == "tuck":   # the first free of the fold, hanging: chosen again whenever it is built
            seg = free_leg(kin, s, FREE_HAND, JointSet(tuple(np.asarray(g, float) for g in rest_goals)), stage,
                           q_from=q)
        else:                                               # slide_open_hand
            seg = Segment(stage, FREE_HAND, q, kind="action", action=("grip", SLIDE_OPEN, 40, False))
            s = with_width(s, side, SLIDE_OPEN)
        times[stage] = round(time.time() - t0, 3)
        if isinstance(seg, Failure):
            return Failure(seg.why, seg.segment, {"stage_s": times, "partial": built_so_far(segs, side, decided)})
        segs.append(seg)
        q = seg.q_end
    return Plan(tuple(sided(sg, side) for sg in segs), info={"stage_s": times}, decisions=decided)


STIR_STAGES = ("stir_arrive", "stir_reach", "stir_dip", "stir_circle", "stir_stirred", "stir_leave", "stir_back")
STIR_ANCHORS = ("stir_arrive", "stir_stirred")   # the base, the pot and the spoon as they are; after the circle
STIR_RELAY = "stir_reach"     # what the park search's ranking IK solves: the dip's end (the tip at the circle's start,
                              # in the pot) -- a seed of the reach's IK at the dip's start, as SLIDE_RELAY
STIR_STEP = 2 * np.pi / 24    # rad of the circle between the task segment's checked samples (docs 2.4: by angle; the
                              # old stir moved through 16 points a turn and checked none)


def stir_tcp(stir, s):
    """The TCP's pose (4x4) in the pot's box frame with the tip at angle ``s`` of the circle: the tip at
    stir["c"] + stir["r"] (cos s ex + sin s ey) -- ex, ey (stir["axes"], default the frame's x and y) the
    world's horizontal x and y written in the pot's frame, so the circle is level however that frame is
    turned -- the TCP turned stir["R"] there (the hand's orientation in the pot's frame, the spoon tilted),
    stir["t_tool"] the tip in the TCP frame (skill_jobs.tool.tool_in_tcp)."""
    R = np.asarray(stir["R"], float)
    ex, ey = (np.asarray(v, float) for v in stir.get("axes", ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0))))
    tip = np.asarray(stir["c"], float) + float(stir["r"]) * (np.cos(s) * ex + np.sin(s) * ey)
    T = np.eye(4)
    T[:3, :3], T[:3, 3] = R, tip - R @ np.asarray(stir["t_tool"], float)
    return T


def in_pot(side, stir):
    """The Spec of the motions in the pot: the spoon and the fingers holding it may touch the pot and what is
    in it (Spec.touch (name, "held"): the held link and the fingers off against those, the rest of the arm
    checked against them as ever); the monitor told the same (the load on the pot, Allow.held_on)."""
    names = tuple(stir["touch"])
    return Spec(allow=Allow(hand=side, links="fingers", touch=names, held_on=names,
                            reason="stir: the spoon and its fingers in the pot and among what is in it"),
                fingers=True, exempt=False, touch=tuple((n, "held") for n in names))


def plan_stir(kin, state, stir, start="stir_arrive", prior=None, step=0.003):
    """The spoon in ``kin``'s hand stirred round inside the pot stir["pot"] from ``state``: stir = {pot, c, r,
    R, t_tool (stir_tcp), turns (0: a dip, no circle), above (m the dip comes straight down), touch (what the
    spoon may touch in the pot: the pot and what is in it)}:

        stir_arrive   anchor: the base, the pot and the hold as they are
        stir_reach    the free leg to ``above`` over the dip's end (decide_ik: _reach), the spoon tilted as it
                      will stir -- free space, the load's tilt not held: a tool is turned on purpose (the one
                      tilt rule of a carry, kinematics.carry_tilt_allowed, is for loads that must stay level)
        stir_dip      the straight down: the tip into the pot at the circle's start (in_pot)
        stir_circle   the task segment (Script, primitives.Still: the pot stays, its frame the TCP's): the tip
                      round the circle stir["turns"] times, the arm's IK continued (carry "arm"), checked whole
                      -- all or nothing (in_pot)
        stir_stirred  anchor: the pot and the spoon after the circle
        stir_leave    the straight back up ``above`` (in_pot: it starts among what is in the pot)
        stir_back     the free leg back to the arm's posture where the stir arrived (the carry it came in, a
                      decision of the plan: rebuilt later, the one the first build recorded), the tilt not held

    The reach and the dip carry the Aim (the TCP at the circle's start in the pot's frame) and STIR_TOL
    (primitives.holds checks them again).  From ``start`` on; ``prior`` as plan_slide's (a Plan: its motions
    that still hold kept, its decisions tried first; else the park search's ranking solution of the dip's
    end, STIR_RELAY).  Plan or Failure."""
    with query(kin, state, FREE_HAND):          # kin.tcp at the state's base throughout
        return _plan_stir(kin, state, stir, start, prior, step)


def _plan_stir(kin, state, stir, start, prior_plan, step):
    i0 = STIR_STAGES.index(start)
    prior = decisions_of(prior_plan)
    pot, side = stir["pot"], kin.side
    up = np.array([0.0, 0.0, 1.0])
    above, turns = float(stir["above"]), float(stir["turns"])
    if state.held(side) is None:
        return Failure("nothing in the hand to stir with", start)
    aim = Aim(pot, stir_tcp(stir, 0.0), side=side)
    aimed = aim_pose(state, aim)
    if aimed is None and i0 <= STIR_STAGES.index("stir_circle"):
        return Failure(f"{pot} is not in the State", start)
    p, R = aimed if aimed is not None else (None, None)
    spec = in_pot(side, stir)
    q, s = state.q(side), state
    back = prior.get("stir_back")
    segs, decided, times = [], {}, {}
    if i0 == 0:
        back = np.asarray(q, float).copy()          # the posture it arrives in: where stir_back returns
    if back is not None:
        decided["stir_back"] = np.asarray(back, float)
    for stage in STIR_STAGES[i0:]:
        t0 = time.time()
        kept = _kept(kin, s, q, prior_plan, stage) if stage != "stir_back" else None
        if stage in STIR_ANCHORS:
            seg = anchor(stage, q, s, (pot,), side)
        elif stage == "stir_reach":
            seg = kept or _reach(kin, s, FREE_HAND, p, R, -up, above, q, prior.get(stage, prior.get(STIR_RELAY)),
                                 stage, step)
            if not isinstance(seg, Failure):
                seg = kept or _aimed(kin, seg, aim, aimed, STIR_TOL, steps_per_wp=4, smooth=True)
                if seg.qs:                                  # the dip's start as the plan reaches it
                    decided[stage] = seg.q_end
        elif stage == "stir_dip":
            seg = kept or straight(kin, s, spec, p, R, stage, step=step, q_from=q)
            if not (isinstance(seg, Failure) or kept):
                seg = _aimed(kin, seg, aim, aimed, STIR_TOL, steps_per_wp=5)
        elif stage == "stir_circle":
            if turns <= 0:                                  # a dip: no circle
                times[stage] = round(time.time() - t0, 3)
                continue
            script = Script(still(pot), 0.0, 2 * np.pi * turns, step=STIR_STEP,
                            tcp=lambda a: stir_tcp(stir, a), carry="arm")
            seg = kept or scripted(kin, with_arm(s, q, side), spec, script, stage, arm_step=step)
            if not (isinstance(seg, Failure) or kept):
                seg = _move(seg, steps_per_wp=4)
        elif stage == "stir_leave":
            p0, R0 = kin.tcp(q)
            seg = kept or straight(kin, s, spec, np.asarray(p0, float) + above * up, R0, stage, step=step, q_from=q)
            if not (isinstance(seg, Failure) or kept):
                seg = _move(seg, steps_per_wp=4, smooth=True)
        else:                                               # stir_back: chosen again whenever it is built
            if back is None:
                return Failure("no posture to go back to (the stir's arrival not in its plan)", stage,
                               {"stage_s": times})
            seg = free_leg(kin, s, FREE_HAND, JointSet((np.asarray(back, float),)), stage, q_from=q)
            if not isinstance(seg, Failure):
                seg = _move(seg, steps_per_wp=4, smooth=True)
        times[stage] = round(time.time() - t0, 3)
        if isinstance(seg, Failure):
            return Failure(seg.why, seg.segment, {"stage_s": times, "partial": built_so_far(segs, side, decided)})
        segs.append(seg)
        q = seg.q_end
    return Plan(tuple(sided(sg, side) for sg in segs), info={"stage_s": times}, decisions=decided)


PRESS_STAGES = ("press_arrive", "press_reach", "press_close_hand", "press_in", "press_toggle", "press_pressed",
                "press_leave", "tuck", "press_door", "press_door_moved")
PRESS_ANCHORS = ("press_arrive", "press_pressed", "press_door_moved")   # the base as it stopped; the hand where the
#                                                     button stopped it; the door where its motor left it
PRESS_DOOR_STEP = 0.1         # rad of the door's swing between the checked samples (docs 2.4: by angle; not measured)
PRESS_RELAY = "press_end"     # what the park search's ranking IK solves: the press's end (the tips on the button) --
                              # a seed of press_reach's IK at the straight's start, as SLIDE_RELAY


def plan_press(kin, state, press, rest_goals, start="press_arrive", prior=None, step=0.003, base=None):
    """The button press["button"] ("<appliance>/<key>": a collider owner of its own, scene_geometry.buttons)
    pressed by ``kin``'s closed fingertips from ``state``: press = {button, p, R (the TCP where the press ends:
    the tips PRESS_DEPTH into the button's face, the hand turned R -- skill_jobs.press), u (the unit the press
    goes in along: into the button), approach (m: it comes straight in from this far back along u), toggle
    (None, or (appliance, on): what the press switches -- the heat source on / off, Actuator.toggle), seen_as
    (the other names the contact monitor may report a touch of the button by: its annotated obstacle box)}:

        press_arrive      anchor: the base as it stopped
        press_reach       the free leg to ``approach`` in front of the press's end (decide_ik: _reach), the hand
                          as it is
        press_close_hand  close the fingers there, in free space: one blunt tip (closed where the arm stood, they
                          closed on the pot it had just set on the stove: T07 microwave_holds_pot, 11-24)
        press_in          the straight in: the fingertips onto the button and PRESS_DEPTH into its face (they
                          may touch the button, nothing else of the appliance: Spec.touch)
        press_toggle      the appliance switched (an action; none when press["toggle"] is None)
        press_pressed     anchor: where the button stopped the hand
        press_leave       out of the contact: straight back along -u as far as contact_extent measures
                          (near_world: LEAVE_GAP clear, then LEAVE_MARGIN)
        tuck              the first free of ``rest_goals`` (JointSet; never kept)
        press_door        the key's door driven by its motor to press["door"]["to"] (an action, drive_part) --
                          only where the robot, as the tuck leaves it, stands clear of the door all along its
                          swing (every PRESS_DOOR_STEP: the base by ``base``, BaseModel.clear; the arm, free_at
                          with both arms still, as a ride checks it); none when press["door"] is None
        press_door_moved  anchor: where the door went

    The button is static (the appliance's body): no Aim -- the press's end is a world pose.  From ``start``
    on; ``prior`` as plan_slide's (a Plan: its motions that still hold kept, its decisions tried first; else
    the park search's ranking solution of the press's end, PRESS_RELAY).  Plan or Failure."""
    with query(kin, state, FREE_HAND):          # kin.tcp at the state's base throughout
        return _plan_press(kin, state, press, rest_goals, start, prior, step, base)


def _sweep_clear(kin, state, part, v0, v1, q, base):
    """Why the robot (the arm at q, the base where ``state`` has it) is not clear of ``part`` swinging from v0 to
    v1, or None: the base (BaseModel.clear) and the arm (free_at, both arms still) at every PRESS_DOOR_STEP."""
    n = max(2, int(np.ceil(abs(v1 - v0) / PRESS_DOOR_STEP)) + 1)
    spec = Spec(arms_still=True)
    for v in np.linspace(v0, v1, n):
        st = with_part(state, part, float(v))
        if base is not None and not base.clear(st, [st.base])[0]:
            return f"the base is in its way at {v:.2f}"
        if not free_at(kin, st, spec, q):
            return f"the arm is in its way at {v:.2f}"
    return None


def _plan_press(kin, state, press, rest_goals, start, prior_plan, step, base):
    i0 = PRESS_STAGES.index(start)
    prior = decisions_of(prior_plan)
    side, button = kin.side, press["button"]
    p, R = np.asarray(press["p"], float), np.asarray(press["R"], float)
    u = np.asarray(press["u"], float)
    # the planner's button (Spec.touch); the monitor names a touch of it by the button's own annotated box as well
    names = (button,) + tuple(n for n in press.get("seen_as", ()) if n != button)
    on_it = Spec(allow=Allow(hand=side, links="fingers", touch=names, reason="the closed fingertips pressing the button"),
                 fingers=True, exempt=False, touch=((button, "fingers"),))
    q, s = state.q(side), state
    segs, decided, times = [], {}, {}
    for stage in PRESS_STAGES[i0:]:
        t0 = time.time()
        kept = _kept(kin, s, q, prior_plan, stage) if stage != "tuck" else None
        if stage in PRESS_ANCHORS and stage != "press_door_moved":
            seg = anchor(stage, q, s, (), side)
        elif stage == "press_close_hand":
            seg = Segment(stage, FREE_HAND, q, kind="action", action=("grip", 0.0, None, False))   # closed: as slide's
            s = with_width(s, side, 0.0)
        elif stage == "press_reach":
            seg = kept or _reach(kin, s, FREE_HAND, p, R, u, float(press["approach"]), q,
                                 prior.get(stage, prior.get(PRESS_RELAY)), stage, step)
            if not isinstance(seg, Failure) and seg.qs:     # the straight's start as the plan reaches it
                decided[stage] = seg.q_end
        elif stage == "press_in":
            seg = kept or straight(kin, s, on_it, p, R, stage, step=step, q_from=q)
            if not (isinstance(seg, Failure) or kept):
                seg = _move(seg, steps_per_wp=4)
        elif stage == "press_toggle":
            if press.get("toggle") is None:
                times[stage] = round(time.time() - t0, 3)
                continue
            app, on = press["toggle"]
            seg = Segment(stage, on_it, q, kind="action", action=("toggle", str(app), bool(on)))
        elif stage == "press_leave":
            seg = kept or _contact(kin, s, Spec(allow=LEAVE_CONTACT), -u, "near_world", stage, step, q,
                                   steps_per_wp=3, smooth=True)
            if not isinstance(seg, Failure) and not seg.qs:    # touching nothing: no exit
                times[stage] = round(time.time() - t0, 3)
                continue
        elif stage == "press_door":
            door = press.get("door")
            if door is None:
                times[stage] = round(time.time() - t0, 3)
                continue
            v0 = s.parts.get(door["part"])
            if v0 is None:
                return Failure(f"{door['part']} is not in the State", stage, {"stage_s": times})
            why = _sweep_clear(kin, s, door["part"], float(v0), float(door["to"]), q, base)
            if why is not None:
                seg = Failure(f"{door['part']} swinging to {float(door['to']):.2f}: {why}", stage)
            else:
                seg = Segment(stage, Spec(), q, kind="action", action=("drive_part", door["part"], float(door["to"])))
                s = with_part(s, door["part"], float(door["to"]))
        elif stage == "press_door_moved":
            if press.get("door") is None:
                times[stage] = round(time.time() - t0, 3)
                continue
            seg = anchor(stage, q, s, (press["door"]["part"],), side)
        else:                   # tuck: the first free of the fold, hanging -- chosen again whenever it is built
            seg = free_leg(kin, s, FREE_HAND, JointSet(tuple(np.asarray(g, float) for g in rest_goals)), stage,
                           q_from=q)
        times[stage] = round(time.time() - t0, 3)
        if isinstance(seg, Failure):
            return Failure(seg.why, seg.segment, {"stage_s": times, "partial": built_so_far(segs, side, decided)})
        segs.append(seg)
        q = seg.q_end
    return Plan(tuple(sided(sg, side) for sg in segs), info={"stage_s": times}, decisions=decided)


WIPE_STAGES = ("wipe_arrive", "wipe_reach", "wipe_press", "wipe_stroke", "wipe_return", "wipe_wiped", "wipe_leave",
               "wipe_back")
WIPE_ANCHORS = ("wipe_arrive", "wipe_wiped")   # the base and the hold as they are; after the strokes
WIPE_RELAY = "wipe_reach"     # what the park search's ranking IK solves: the press's pose at the strip's start (the
                              # sponge pressed on) -- a seed of the reach's IK at the descent's start, as STIR_RELAY
WIPE_STEP = 0.02              # m of the stroke between the task segment's checked samples (docs 2.4: by travel)


def on_surface(side, support):
    """The Spec of the motions with the sponge on the support: it and the fingers holding it may touch the support
    (Spec.touch (name, "held"): static furniture by name, Motion._touch_key), the rest of the arm checked against it
    as ever; the monitor told the same (the load on the support, Allow.held_on)."""
    return Spec(allow=Allow(hand=side, links="fingers", touch=(support,), held_on=(support,),
                            reason="wipe: the sponge pressed on the support, the fingers holding it"),
                fingers=True, exempt=False, touch=((support, "held"),), hold_tilt=True)


def plan_wipe(kin, state, wipe, start="wipe_arrive", prior=None, step=0.004):
    """The sponge in ``kin``'s hand wiped along a strip of the support wipe["support"] from ``state``: wipe =
    {support, aim (motion_state.Aim, held: the sponge's box frame where it is pressed WIPE_PRESS into the surface at
    the strip's start -- the TCP derived from the hold the State has, as a place's set-down; or p, R: that TCP given),
    d (the stroke: the horizontal world vector from the strip's start to its end), above (m the press comes straight
    down from: the sponge LEAVE_GAP + LEAVE_MARGIN clear of the surface there), need (m the stroke must run)}:

        wipe_arrive  anchor: the base and the hold as they are
        wipe_reach   the free leg to ``above`` over the press (decide_ik: _reach), the sponge's tilt held
        wipe_press   the straight down: the sponge onto the surface, WIPE_PRESS into it (on_surface)
        wipe_stroke  the task segment (Script, primitives.Still in the world's frame: nothing moves; carry "arm"):
                     the TCP along d, the arm's IK continued, checked whole -- as far as the arm reaches
                     (scripted's reach: the stroke's length measured, not set); shorter than wipe["need"] (m, the
                     job's: enough for the coverage asked) a Failure -- the search and a rebuild alike (rule 2)
        wipe_return  the task segment back to the strip's start (the second pass)
        wipe_wiped   anchor: the base and the hold after the strokes
        wipe_leave   the straight back up ``above`` (on_surface: it starts on the surface)
        wipe_back    the free leg back to the arm's posture where the wipe arrived (stir_back's rule), tilt held

    The reach and the press carry the Aim and WIPE_TOL (Segment.info: primitives.holds checks them again against the
    State, so a sponge that slid in the hand on the way rebuilds the press from the arrival on, rule 9).  The old
    WipeSurfacePolicy held the arm still and translated the base along the strip, the press a move_to with an
    approach and a hand-written 8 cm lift: one task segment on the arm instead (HAND_PLAN 9g).  From ``start`` on;
    ``prior`` as plan_stir's.  Plan or Failure; info["stroke_m"] the stroke the plan makes."""
    with query(kin, state, FREE_HAND):          # kin.tcp at the state's base throughout
        return _plan_wipe(kin, state, wipe, start, prior, step)


def _plan_wipe(kin, state, wipe, start, prior_plan, step):
    from ._common import FREE_LOAD
    i0 = WIPE_STAGES.index(start)
    prior = decisions_of(prior_plan)
    side, support = kin.side, wipe["support"]
    up = np.array([0.0, 0.0, 1.0])
    above = float(wipe["above"])
    if state.held(side) is None:
        return Failure("nothing in the hand to wipe with", start)
    aim = wipe.get("aim")
    aimed = aim_pose(state, aim) if aim is not None else (np.asarray(wipe["p"], float), np.asarray(wipe["R"], float))
    if aimed is None:
        return Failure(f"{aim.obj} is not in the {side} hand", start)
    p, R = np.asarray(aimed[0], float), np.asarray(aimed[1], float)
    d = np.asarray(wipe["d"], float)
    length = float(np.linalg.norm(d))
    u = d / length

    def tcp(s):
        T = np.eye(4)
        T[:3, :3], T[:3, 3] = R, p + s * u
        return T
    spec = on_surface(side, support)
    q, s = state.q(side), state
    back = prior.get("wipe_back")
    reached = prior.get("wipe_stroke_m")
    segs, decided, times = [], {}, {}
    if i0 == 0:
        back = np.asarray(q, float).copy()
    if back is not None:
        decided["wipe_back"] = np.asarray(back, float)
    for stage in WIPE_STAGES[i0:]:
        t0 = time.time()
        kept = _kept(kin, s, q, prior_plan, stage) if stage != "wipe_back" else None
        if stage in WIPE_ANCHORS:
            seg = anchor(stage, q, s, (), side)
        elif stage == "wipe_reach":
            seg = kept or _reach(kin, s, FREE_LOAD, p, R, -up, above, q, prior.get(stage), stage, step)
            if not (isinstance(seg, Failure) or kept) and aim is not None:
                seg = _aimed(kin, seg, aim, (p, R), WIPE_TOL)
            if not isinstance(seg, Failure) and seg.qs:
                decided[stage] = seg.q_end
        elif stage == "wipe_press":
            seg = kept or straight(kin, s, spec, p, R, stage, step=0.002, q_from=q)
            if not (isinstance(seg, Failure) or kept):
                seg = _move(seg, steps_per_wp=5)
                if aim is not None:
                    seg = _aimed(kin, seg, aim, (p, R), WIPE_TOL)
        elif stage == "wipe_stroke":
            script = Script(still(None), 0.0, length, step=WIPE_STEP, tcp=tcp, carry="arm")
            seg = kept or scripted(kin, with_arm(s, q, side), spec, script, stage, arm_step=step, reach=True)
            if not (isinstance(seg, Failure) or kept):
                seg = _move(seg, steps_per_wp=6)
            if not isinstance(seg, Failure):
                reached = float(seg.info["script"].s1)
                decided["wipe_stroke_m"] = reached
                if reached < float(wipe.get("need", 0.0)):
                    seg = Failure(f"the arm strokes {reached:.3f} m of the strip, {float(wipe['need']):.3f} m needed",
                                  stage)
        elif stage == "wipe_return":
            if not reached:
                times[stage] = round(time.time() - t0, 3)
                continue
            script = Script(still(None), float(reached), 0.0, step=WIPE_STEP, tcp=tcp, carry="arm")
            seg = kept or scripted(kin, with_arm(s, q, side), spec, script, stage, arm_step=step)
            if not (isinstance(seg, Failure) or kept):
                seg = _move(seg, steps_per_wp=6)
        elif stage == "wipe_leave":
            p0, R0 = kin.tcp(q)
            seg = kept or straight(kin, s, spec, np.asarray(p0, float) + above * up, R0, stage, step=step, q_from=q)
            if not (isinstance(seg, Failure) or kept):
                seg = _move(seg, steps_per_wp=4, smooth=True)
        else:                                               # wipe_back: chosen again whenever it is built
            if back is None:
                return Failure("no posture to go back to (the wipe's arrival not in its plan)", stage,
                               {"stage_s": times})
            seg = free_leg(kin, s, FREE_LOAD, JointSet((np.asarray(back, float),)), stage, q_from=q)
            if not isinstance(seg, Failure):
                seg = _move(seg, steps_per_wp=4, smooth=True)
        times[stage] = round(time.time() - t0, 3)
        if isinstance(seg, Failure):
            return Failure(seg.why, seg.segment, {"stage_s": times, "partial": built_so_far(segs, side, decided)})
        segs.append(seg)
        q = seg.q_end
    return Plan(tuple(sided(sg, side) for sg in segs), info={"stage_s": times, "stroke_m": reached},
                decisions=decided)


ARC_STEP = np.radians(5.0)    # rad of a flip's / pour's arc between the task segment's checked samples (docs 2.4)


def _arc(T0, pivot, axis):
    """tcp(a): the TCP pose ``T0`` (4x4, world) turned by angle a about the line through ``pivot`` along the unit
    ``axis`` -- what a hand holding a load turned about that line does (the world's frame: Still(None))."""
    from scipy.spatial.transform import Rotation
    T0, pivot, axis = np.asarray(T0, float), np.asarray(pivot, float), np.asarray(axis, float)

    def tcp(a):
        Rot = Rotation.from_rotvec(axis * float(a)).as_matrix()
        T = np.eye(4)
        T[:3, :3], T[:3, 3] = Rot @ T0[:3, :3], pivot + Rot @ (T0[:3, 3] - pivot)
        return T
    return tcp


FLIP_STAGES = ("flip_arrive", "flip_arc", "flip_release", "flip_push", "flip_leave", "tuck", "flip_settle")
FLIP_SETTLE = 150             # physics ticks the turned object settles before it is judged (the old flip's)


def plan_flip(kin, state, flip, rest_goals, start="flip_arrive", prior=None, step=0.004):
    """An edge-held flat object turned over by pivoting it about its far edge (HAND_PLAN 9h; the old FlipFlatPolicy):
    flip = {obj, support (what it rests on: its far edge stays on it), pivot, axis (the far edge's line on the
    support), release (rad: the arc goes this far at most), past (rad: past vertical -- released short of it, the open
    hand pushes on), push_to (rad: the push's end), pre_open (m per finger)}:

        flip_arrive   anchor: the base and the hold as they are
        flip_arc      task segment: the gripped near edge up and over on the arc about the pivot, the hand turning with
                      it, the load's tilt not held (it is the motion) and its far edge on the support (Spec.touch,
                      "held") -- as far as the arm reaches, up to ``release`` (scripted's reach: measured); short of
                      flip["min_arc"] a Failure, the search and a rebuild alike (rule 2)
        flip_release  the hand opened (the fingers may touch it)
        flip_push     released short of ``past``: the open hand on along the same arc to ``push_to``, its rotation as
                      at the release, the fingers on the raised edge (none when past)
        flip_leave    out of the contact back along the gripper axis, as far as contact_extent measures
        tuck          the first free of ``rest_goals``
        flip_settle   the object settles

    The old flip's straight pushes in three lengths, its base drives and its swallowed withdraw are gone.  ``prior``,
    ``start``: run's rebuild.  Plan or Failure; info["arc_rad"] how far the arc goes."""
    with query(kin, state, FREE_HAND):
        return _plan_flip(kin, state, flip, rest_goals, start, prior, step)


def _plan_flip(kin, state, flip, rest_goals, start, prior_plan, step):
    from ..motion_state import released
    from ._common import held_frame
    i0 = FLIP_STAGES.index(start)
    side, obj, support = kin.side, flip["obj"], flip["support"]
    held = state.held(side)
    if held is None and i0 <= FLIP_STAGES.index("flip_arc"):
        return Failure("nothing in the hand to flip", start)
    on = Spec(allow=Allow(hand=side, links="fingers", touch=(obj, support), held_on=(support,),
                          reason="flip: the held book's far edge on its support, the fingers on the book"),
              fingers=True, exempt=False, touch=((support, "held"),))
    open_on = Spec(allow=Allow(hand=side, links="fingers", touch=(obj, support), held_on=(),
                               reason="flip: the open fingers push the raised edge over"),
                   fingers=True, exempt=False, touch=((obj, "fingers"),))
    q, s = state.q(side), state
    segs, times = [], {}
    reached = decisions_of(prior_plan).get("flip_arc_rad")
    decided = {}
    for stage in FLIP_STAGES[i0:]:
        t0 = time.time()
        # a motion of the prior that still holds from here is kept as it is (docs 8.3), the tuck chosen again
        kept = _kept(kin, s, q, prior_plan, stage) if stage in ("flip_arc", "flip_push", "flip_leave") else None
        if stage == "flip_arrive":
            seg = anchor(stage, q, s, (obj,), side)
        elif stage == "flip_arc":
            p0, R0 = kin.tcp(q)
            T0 = np.eye(4)
            T0[:3, :3], T0[:3, 3] = R0, p0
            script = Script(still(None), 0.0, float(flip["release"]), step=ARC_STEP,
                            tcp=_arc(T0, flip["pivot"], flip["axis"]), carry="arm")
            seg = kept or scripted(kin, with_arm(s, q, side), on, script, stage, arm_step=step, reach=True)
            if not (isinstance(seg, Failure) or kept):
                seg = _move(seg, steps_per_wp=4, smooth=True)
            if not isinstance(seg, Failure):
                reached = float(seg.info["script"].s1)
                decided["flip_arc_rad"] = reached
                if reached < float(flip.get("min_arc", 0.0)):
                    seg = Failure(f"the arm turns it only {np.degrees(reached):.0f} deg "
                                  f"({np.degrees(float(flip['min_arc'])):.0f} needed)", stage)
        elif stage == "flip_release":
            seg = Segment(stage, open_on, q, kind="action", action=("grip", float(flip["pre_open"]), 50, False))
            if held is not None:
                s = released(s, side, held.name, held_frame(kin, q, held))
            s = with_width(s, side, float(flip["pre_open"]))
        elif stage == "flip_push":
            if reached is None or reached >= float(flip["past"]):
                times[stage] = round(time.time() - t0, 3)
                continue
            p0, R0 = kin.tcp(q)
            # the open hand's position on along the arc, its rotation kept as it let go
            arc = _arc(np.r_[np.c_[R0, p0], [[0, 0, 0, 1]]], flip["pivot"], flip["axis"])

            def tcp(a, arc=arc, R0=R0, r0=reached):
                T = arc(a - r0)
                T[:3, :3] = R0
                return T
            script = Script(still(None), float(reached), float(flip["push_to"]), step=ARC_STEP, tcp=tcp, carry="arm")
            seg = kept or scripted(kin, with_arm(s, q, side), open_on, script, stage, arm_step=step)
            if not (isinstance(seg, Failure) or kept):
                seg = _move(seg, steps_per_wp=4, smooth=True)
        elif stage == "flip_leave":
            _, R0 = kin.tcp(q)
            seg = kept or _contact(kin, s, Spec(allow=LEAVE_CONTACT), np.asarray(R0, float)[:, 2], "near_world", stage,
                                   step, q, steps_per_wp=3, smooth=True)
            if not isinstance(seg, Failure) and not seg.qs:
                times[stage] = round(time.time() - t0, 3)
                continue
        elif stage == "tuck":
            seg = free_leg(kin, s, FREE_HAND, JointSet(tuple(np.asarray(g, float) for g in rest_goals)), stage, q_from=q)
        else:
            seg = Segment(stage, Spec(), q, kind="action", action=("wait", FLIP_SETTLE))
        times[stage] = round(time.time() - t0, 3)
        if isinstance(seg, Failure):
            return Failure(seg.why, seg.segment, {"stage_s": times, "partial": built_so_far(segs, side, decided)})
        segs.append(seg)
        q = seg.q_end
    return Plan(tuple(sided(sg, side) for sg in segs), info={"stage_s": times, "arc_rad": reached}, decisions=decided)


POUR_STAGES = ("pour_arrive", "pour_reach", "pour_tilt", "pour_hold", "pour_untilt", "pour_back")
POUR_RELAY = "pour_reach"     # what the park search's ranking IK solves: the pose over the target the tilt starts at
POUR_HOLD = 180               # physics ticks the cup is held tilted (the old pour's wait)


def plan_pour(kin, state, pour, start="pour_arrive", prior=None, step=0.004):
    """The held cup pour["source"] poured into pour["target"] (HAND_PLAN 9h; the old PourIntoPolicy): pour = {source,
    target, p, R (the TCP over the target the tilt starts at), pivot (the point the cup turns about: half-way from the
    hand to its lip), axis (horizontal, across the pour), tilt (rad: at most)}:

        pour_arrive  anchor: the base and the hold as they are
        pour_reach   the free leg to (p, R), the cup's tilt held (decide_ik: _reach, no straight)
        pour_tilt    task segment: the cup turned about the pivot, the hand with it, the load's tilt not held (it is the
                     motion) -- as far as the arm reaches, up to ``tilt`` (scripted's reach: measured); short of
                     pour["min_tilt"] a Failure, the search and a rebuild alike (rule 2)
        pour_hold    the contents fall out
        pour_untilt  task segment: back the same arc to upright
        pour_back    the free leg back to the arm's posture where the pour arrived (stir_back's rule), tilt held

    The old pour's 7 tilts x 10 wrist turns tried for parks one after another, its held_vertical_move raise, its
    re-measured pose and fallback to the planned one, and its 20-degree move_to steps are gone.  Plan or Failure;
    info["tilt_rad"] how far it tilts."""
    with query(kin, state, FREE_HAND):
        return _plan_pour(kin, state, pour, start, prior, step)


def _plan_pour(kin, state, pour, start, prior_plan, step):
    from ._common import FREE_LOAD
    i0 = POUR_STAGES.index(start)
    prior = decisions_of(prior_plan)
    side = kin.side
    if state.held(side) is None:
        return Failure("nothing in the hand to pour from", start)
    p, R = np.asarray(pour["p"], float), np.asarray(pour["R"], float)
    T0 = np.eye(4)
    T0[:3, :3], T0[:3, 3] = R, p
    tcp = _arc(T0, pour["pivot"], pour["axis"])
    free = Spec(fingers=True, exempt=False)          # a load turned on purpose: its tilt not held
    q, s = state.q(side), state
    back = prior.get("pour_back")
    reached = prior.get("pour_tilt_rad")
    segs, decided, times = [], {}, {}
    if i0 == 0:
        back = np.asarray(q, float).copy()
    if back is not None:
        decided["pour_back"] = np.asarray(back, float)
    for stage in POUR_STAGES[i0:]:
        t0 = time.time()
        kept = _kept(kin, s, q, prior_plan, stage) if stage != "pour_back" else None
        if stage == "pour_arrive":
            seg = anchor(stage, q, s, (pour["source"],), side)
        elif stage == "pour_reach":
            seg = kept or _reach(kin, s, FREE_LOAD, p, R, np.array([0.0, 0.0, -1.0]), 0.0, q,
                                 prior.get(stage), stage, step)
            if not isinstance(seg, Failure) and seg.qs:
                decided[stage] = seg.q_end
        elif stage == "pour_tilt":
            script = Script(still(None), 0.0, float(pour["tilt"]), step=ARC_STEP, tcp=tcp, carry="arm")
            seg = kept or scripted(kin, with_arm(s, q, side), free, script, stage, arm_step=step, reach=True)
            if not (isinstance(seg, Failure) or kept):
                seg = _move(seg, steps_per_wp=5, smooth=True)
            if not isinstance(seg, Failure):
                reached = float(seg.info["script"].s1)
                decided["pour_tilt_rad"] = reached
                if reached < float(pour.get("min_tilt", 0.0)):
                    seg = Failure(f"the arm tilts it only {np.degrees(reached):.0f} deg "
                                  f"({np.degrees(float(pour['min_tilt'])):.0f} needed)", stage)
        elif stage == "pour_hold":
            seg = Segment(stage, Spec(), q, kind="action", action=("wait", POUR_HOLD))
        elif stage == "pour_untilt":
            if not reached:
                times[stage] = round(time.time() - t0, 3)
                continue
            # back the same arc from where the tilt left the hand (its pose, not the tilt's planned end)
            pq, Rq = kin.tcp(q)
            Tq = np.eye(4)
            Tq[:3, :3], Tq[:3, 3] = Rq, pq
            script = Script(still(None), 0.0, -float(reached), step=ARC_STEP, tcp=_arc(Tq, pour["pivot"], pour["axis"]),
                            carry="arm")
            seg = kept or scripted(kin, with_arm(s, q, side), free, script, stage, arm_step=step)
            if not (isinstance(seg, Failure) or kept):
                seg = _move(seg, steps_per_wp=6, smooth=True)
        else:
            if back is None:
                return Failure("no posture to go back to (the pour's arrival not in its plan)", stage,
                               {"stage_s": times})
            seg = free_leg(kin, s, FREE_LOAD, JointSet((np.asarray(back, float),)), stage, q_from=q)
            if not isinstance(seg, Failure):
                seg = _move(seg, steps_per_wp=4, smooth=True)
        times[stage] = round(time.time() - t0, 3)
        if isinstance(seg, Failure):
            return Failure(seg.why, seg.segment, {"stage_s": times, "partial": built_so_far(segs, side, decided)})
        segs.append(seg)
        q = seg.q_end
    return Plan(tuple(sided(sg, side) for sg in segs), info={"stage_s": times, "tilt_rad": reached}, decisions=decided)
