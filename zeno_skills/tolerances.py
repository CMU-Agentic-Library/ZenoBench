"""The thresholds of the motion layers' error model, one source each (docs/motion/MOTION_ARCHITECTURE.md
4.5): the error bounds of the anchors (8.2), what a segment is checked again by (8.4), and the
contact geometry the primitives measure by (5.1-5.3).  Each with its unit and where its value comes
from (``src``) -- measured, estimated, chosen, or inherited and never measured -- so which numbers
stand on data can be read here, not dug out of four files.  The modules that use them import them
from here (primitives re-exports its own: code and tests that read ``primitives.TARGET_TOL`` keep
working).  Leaf module: imports nothing of zeno_skills.

What sets the open ones: 9.3 step 2.1, the anchors' and segments' logs (run.py: anchor ``off``,
segment ``aim_off``; skill_jobs.pick ``held_offset``) aggregated by tools/anchor_stats.py.

Also here (second batch, 11-11): the planner's collision model and the contact monitor's
thresholds, what a skill's hooks judge a pick / place / door by, and the execution's "arrived" /
"stalled" -- each the one value its users share (the same literal written twice became one name).

Not here: execution parameters (speeds, smooth, steps_per_wp: Segment.info), search budgets and
costs (park_search, skills), the task predicates' thresholds (predicates.py: the evaluation, not the
motion), and the old code's own thresholds (skills, policies) -- those go with the migration of what
uses them (the perception skills': 11-16, the exploration section -- with their sweep's head angles and ticks: a
look's plan takes them as aims, there is no Segment.info to hold them yet; visual prompting's: the last section)."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Tol:
    value: object                    # float, (m, rad), or None: not set yet
    unit: str
    src: str


TOLS: dict[str, Tol] = {}


def _t(name, value, unit, src):
    TOLS[name] = Tol(value, unit, src)
    return value


# --------------------------------------------------------------- contact geometry (5.1-5.3)
LEAVE_GAP = _t("LEAVE_GAP", 0.005, "m", "chosen: closer to the world than this still touches it; a set-down "
               "pose stands this high and the load falls it (COLLISION_PLAN 6); unmeasured")
BODY_GAP = _t("BODY_GAP", LEAVE_GAP, "m", "= LEAVE_GAP: the arms, the hands and what they hold stay this far off the robot's own base (body_collision: its terms' activation, cost and constraint) -- with no margin a load carried flush against the column read as touching it 0.6 mm in at the next motion's start and was left out of the model, then swept through the column (T05 homework_ready, 11-12)")
LEAVE_MARGIN = _t("LEAVE_MARGIN", 0.01, "m", "chosen: a contact exit runs this far past clear (Rig.leave's "
                  "1 cm, inherited); unmeasured")
LEAVE_MAX = _t("LEAVE_MAX", 0.06, "m", "chosen: a contact exit runs no further (Rig.leave's 6 cm, inherited)")
ON_LINE = _t("ON_LINE", 0.005, "m", "chosen: a TCP this close to a straight is on it; unmeasured")
ON_LINE_TURN = _t("ON_LINE_TURN", 0.01, "rad", "chosen: ...turned this little from it; unmeasured")
JOINT_GOAL_TOL = _t("JOINT_GOAL_TOL", 0.01, "rad", "chosen: a planned leg this close to its joint goal ends "
                    "at it; unmeasured")
HINT_REACH = _t("HINT_REACH", 0.001, "m", "chosen: a decided solution whose TCP is this close to its pose "
                "still decides it (decide_ik); unmeasured")
HINT_TURN = _t("HINT_TURN", 0.01, "rad", "chosen: ...turned this little; unmeasured")
# a door pushed shut (skill_jobs.door.close_job, skill_plans.plan_push; docs 6, close)
PUSH_ABOVE = _t("PUSH_ABOVE", 0.13, "m", "inherited (skills' old _push_targets): the push point this far above the "
                "handle centre, clear of the bar -- or as far below it (skill_jobs.door.PUSH_HEIGHTS: under a "
                "counter's lip the gripper and its camera hit the lip above, 11-12 T02 / T05 / T19)")
PUSH_PRE = _t("PUSH_PRE", 0.10, "m", "inherited (skills' old push): the push comes in from this far off the panel")
PUSH_TIP_GAP = _t("PUSH_TIP_GAP", 0.012, "m", "inherited (skills' old _push_targets): the closed fingertips' TCP "
                  "this far off the panel face where the push-in ends")
PUSH_TRACK = _t("PUSH_TRACK", (0.03, 0.25), "rad, rad/s", "inherited (skills._ride's lead and rate): the ride "
                "of a push keeps the hand at most a lead ahead into the panel")
BODY_SAME = _t("BODY_SAME", 0.01, "m", "chosen, unmeasured: a torso this close to the height a push's push_body "
               "would take it to stays (no leg)")

# --------------------------------------------------------------- error bounds of the anchors (8.2)
BASE_TOL = _t("BASE_TOL", 0.007, "m", "estimated: the base stopping off its park, COLLISION_PLAN 8, not "
              "measured closely (sim logs: within 1 mm); not used in code yet -- the base error is rebuilt "
              "from (PICK_TOL / PLACE_TOL), no margin; set from anchor_stats 1 (*_arrive base)")
HELD_POSE_MARGIN = _t("HELD_POSE_MARGIN", 0.005, "m", "first value: a pick's carry planned before the close "
                      "rides on the assumed hold (T01 overhang_ready 11-08 collided by 0 mm with none); set "
                      "from anchor_stats 1 (pick_held hold) / 3 (held_offset) -- rim_pinch reached 21.5 mm "
                      "on 11-11")
HOLD_DRIFT = _t("HOLD_DRIFT", None, "m", "to measure: the load slipping in the hand while driving, under the "
                "physical profile (sticky hands weld it); anchor_stats 1 (place_arrive / arrive hold)")

# --------------------------------------------------------------- checks of a segment (8.4)
PLAN_AT_START = _t("PLAN_AT_START", 1e-3, "rad", "exact: the commanded arm against a segment's start -- "
                   "command to command (q_cmd), the slack only numerical; also the arm already at its rest "
                   "(plan_navigate's tuck)")
EXTENT_TOL = _t("EXTENT_TOL", LEAVE_MARGIN / 2, "m", "reasoned: a contact exit measured again within this "
                "still clears with half the margin (one 2 mm step was the measure's own resolution: 7 of 13 "
                "rebuilds of the 11-08 run)")
# an object pushed or dragged across its support (skill_jobs.slide, skill_plans.plan_slide; docs 6, contact).  Its
# entry follows a pick's (skills.pick_approach, LEAVE_MARGIN), its exit is measured (contact_extent), its leg is as
# long as the arm reaches: none of those is a constant of its own
SLIDE_PAD_GAP = _t("SLIDE_PAD_GAP", 0.005, "m", "inherited (skills' old push: \"pad bottom ~5 mm above the "
                   "surface\"): the closed fingers' lowest corner this far above the support all along a push -- "
                   "a top pinch's 2 mm (PAD_FLOOR_GAP) made the rest of a push built again at the same pose collide "
                   "between waypoints (T05 notebook, 11-12)")
SLIDE_GAP = _t("SLIDE_GAP", 0.005, "m", "chosen, unmeasured: the planner's closed fingers this far off the back face "
               "where the push-in ends -- with the finger box's excess over the real pads along n (2.7 / 4.2 mm by "
               "the gripper's turn) the hand's lag before the object moves (primitives.Pushed): 7.7 / 9.2 mm; "
               "slide_1112 (11-12) measured 10.7 mm on average (18 pushes, 9-14 mm), the rest unexplained")
TIP_HEIGHT = _t("TIP_HEIGHT", 0.80, "1", "inherited (the old TipOverPolicy's): a tip pokes a standing object at this "
                "fraction of its height -- high enough that it falls rather than slides (HAND_PLAN 9h)")
DRAG_RIM = _t("DRAG_RIM", 0.03, "m", "inherited (skills' old push): a drag presses this far inside the leading rim")
DRAG_PRESS = _t("DRAG_PRESS", 0.006, "m", "inherited (skills' old push: top - 4 mm + 10 mm): a drag's TCP this far "
                "above the top, the fingertips pressed into it (higher only brushes it)")
DRAG_SKID = _t("DRAG_SKID", 0.025, "m", "inherited (skills' old push): a drag's lag -- the hand runs this much "
               "further than the object, the fingertips skid on the top (primitives.Pushed)")
TARGET_TOL = _t("TARGET_TOL", 0.005, "m", "chosen: a hand stopped this far short of where it was sent is "
                "blocked (run: every segment the arm follows, after its hooks -- pick's after_grasp, place's after_down "
                "judge theirs first; Rig._settle measures it; until 11-11 also named skills.PICK_REACH_TOL): reach "
                "errors 0.1-0.4 mm in pick612_verify, 34.6 mm where a finger rode on a mug's wall (T13 no_cup "
                "fingers_cover_1105); the threshold itself unmeasured")
TARGET_TURN = _t("TARGET_TURN", HINT_TURN, "rad", "= HINT_TURN")
PICK_TOL = _t("PICK_TOL", (HINT_REACH, HINT_TURN), "m, rad", "chosen = decide_ik's: a pick's contact segments "
              "further off the grasp than built by more are rebuilt (a chain of fine motions on it); "
              "unmeasured -- anchor_stats 2 (pick_reach / pick_grasp aim_off)")
PLACE_TOL = _t("PLACE_TOL", (TARGET_TOL, TARGET_TURN), "m, rad", "chosen = TARGET_TOL: a set-down less off "
               "only sets the load down a few mm off; unmeasured -- anchor_stats 2 (place_reach / place_down)")
DOOR_TOL = _t("DOOR_TOL", (HINT_REACH, HINT_TURN), "m, rad", "chosen as PICK_TOL (the hook onto a bar is a "
              "fine motion); no sim run yet")
STIR_TOL = _t("STIR_TOL", (TARGET_TOL, TARGET_TURN), "m, rad", "chosen = SLIDE_TOL: the spoon's tip goes 3.5 cm "
              "round inside a pot over 10 cm wide -- a reach or dip a few mm off still stirs inside it; no sim run yet")
STIR_TILT = _t("STIR_TILT", 0.873, "rad", "inherited, unmeasured: the old StirContainerPolicy's tilt_deg 50 -- the "
               "spoon's far end turned down about the horizontal across it, so its bowl reaches below the rim "
               "while the hand stays above it")
STIR_DEPTH = _t("STIR_DEPTH", (0.04, 0.015), "m", "inherited, unmeasured (old StirContainerPolicy): the tip this far "
                "below the rim, at most; and at least this far above the pot's floor (min(0.04, rim - 0.015))")
STIR_RADII = _t("STIR_RADII", (0.035, 0.022, 0.012), "m", "inherited, unmeasured (old StirContainerPolicy): the "
                "tip's circle, the widest a park reaches first (the first capped at 0.45 of the rim's radius); "
                "a tighter circle needs less arm travel and still turns the tip round the pot's centre")
STIR_ABOVE = _t("STIR_ABOVE", 0.06, "m", "inherited, unmeasured (old StirContainerPolicy's 'above'): the dip comes "
                "straight down from where the tip is this far above the rim, and the leave goes back up to it")
PRESS_DEPTH = _t("PRESS_DEPTH", 0.003, "m", "chosen: a press's fingertips go this far into the button's face (its "
                 "collider's front, skill_jobs.press) -- a force's geometric stand-in (COLLISION_PLAN.md section 8): "
                 "the button is rigid, the arm stops where the tips meet it, less than TARGET_TOL short.  The old "
                 "press aimed the TCP 5 mm off the button's centre, the tips 22-29 mm inside it (stopped short, "
                 "accepted up to 35 mm)")
WIPE_PRESS = _t("WIPE_PRESS", 0.001, "m", "inherited: a wipe presses the sponge's bottom this far into the support (the "
                "old WipeSurfacePolicy's light press: a 3 mm press dragged the sponge out of the pinch) -- a force's "
                "geometric stand-in (COLLISION_PLAN.md section 8), HAND_PLAN 9g")
WIPE_TOL = _t("WIPE_TOL", (0.002, TARGET_TURN), "m, rad", "chosen (rule audit 11-25): a wipe's press pose (the "
               "sponge's, through the hold the State has) further off than built by more is rebuilt -- 2 mm on the "
               "WIPE_PRESS of 1 mm presses 3 mm, where the old 3 mm press dragged the sponge out of the pinch; unmeasured")
TOUCH_DEPTH = _t("TOUCH_DEPTH", 0.002, "m", "chosen: a touch's / knock's closed fingertips go this far into the touched "
                 "face (an object's top, a door's panel) -- a force's geometric stand-in (COLLISION_PLAN.md section 8), "
                 "as PRESS_DEPTH: the arm stops where the tips meet it.  The old touch aimed the TCP 1.6 cm over the "
                 "top with the pad tips ~1.8 cm below it (2 mm in, unchecked); the old knock aimed the TCP itself "
                 "4 mm off the panel (the tips well inside it, unchecked) -- HAND_PLAN 9g")
PRESS_APPROACH = _t("PRESS_APPROACH", 0.10, "m", "inherited (old microwave / stove press: the aligned pose 12 cm off "
                    "the button's centre, the press to 5 mm off it): the press comes straight in from this far "
                    "in front of where the tips touch")
SLIDE_TOL = _t("SLIDE_TOL", (TARGET_TOL, TARGET_TURN), "m, rad", "chosen = PLACE_TOL: an object pushed across its "
               "support is a coarse contact -- the push point less off only moves it a few mm otherwise; slide_1112 "
               "(11-12, 12 pushes): the reach, descent and push-in ended at most 0.02 mm further off than built and "
               "the object never moved before the push, so no rebuild came near it -- the bound itself untested")
DOOR_LEAVE = _t("DOOR_LEAVE", 0.17, "m", "chosen from one measurement (11-11, T05 / T20 cabinet_4): let go, the "
                "hinge swings on after the hand (-1.381 -> -1.406 rad); 12 cm back left a finger 1 mm in the door, "
                "14 cm was free (the old path's leave, skills._move_articulated); 3 cm more for other doors")
SAME_POSTURE = _t("SAME_POSTURE", 0.02, "rad", "inherited from the posture chain (ea47359), unmeasured: "
                  "postures no joint of which differs by more are one (no swing, no chain step: plan_navigate, "
                  "skills._base_steps)")
SAME_PARK = _t("SAME_PARK", (1e-4, 1e-2), "m, deg", "exact: two base poses this close are one park (numerical)")
NUMERIC_M = _t("NUMERIC_M", 1e-3, "m", "exact: slack of a length compared command to command (on a straight, "
               "a hand already open that wide: skill_plans._common), numerical only")
MOVED_MM = _t("MOVED_MM", 5.0, "mm", "chosen, logging only: an object other than the watched ones this far off "
              "where a plan assumed it is listed in an anchor's off (motion_state.state_offset)")
REST_TOL = _t("REST_TOL", 0.05, "rad", "inherited, unmeasured: measured torso, waist and arm joints this close to "
              "the rest posture are at rest (skill_runtime, policies.navigation)")
STOWED_TOL = _t("STOWED_TOL", 0.10, "rad", "inherited, unmeasured: ...and arm joints alone this close, the arm is "
                "stowed (skill_runtime)")

# --------------------------------------------------------------- the planner's collision model (4.4)
POS_TOL = _t("POS_TOL", 0.004, "m", "chosen: cuRobo's position_threshold (IK and motion gen): a planned TCP may "
             "end this far off its pose -- the residual holds compares against, not adds (8.4)")
ROT_TOL = _t("ROT_TOL", 0.04, "rad", "chosen: cuRobo's rotation_threshold, as POS_TOL")
ACTIVATION = _t("ACTIVATION", 0.005, "m", "chosen: cuRobo's collision_activation_distance (the collision cost "
                "starts this far out)")
DEPTH_TOL = _t("DEPTH_TOL", 1e-4, "m", "exact: a penetration this shallow is clear (numerical slack of the sphere "
               "queries, not a margin); every whole-body base check compares against it")
FOOTPRINT_MARGIN = _t("FOOTPRINT_MARGIN", 0.046, "m", "inherited, unmeasured: the base keeps this from the boxes "
                      "and moving parts in xy, the one margin (1.6 cm inside BASE_HALF plus 3 cm on top, both from "
                      "3ccd5e99, the sum kept: COLLISION_PLAN 2)")
HELD_SPHERE_OUT = _t("HELD_SPHERE_OUT", 0.004, "m", "chosen < LEAVE_GAP (a set-down's end stays free): a held "
                     "object's spheres stick out of it by at most this; offline 11-11: <= 4.0 mm")
HELD_SPHERE_GAP = _t("HELD_SPHERE_GAP", 0.006, "m", "chosen: no point of a held object's surface further than this "
                     "from its spheres (first try); offline 11-11: <= 6.3 mm")
HELD_SPHERE_GAP_MAX = _t("HELD_SPHERE_GAP_MAX", 0.02, "m", "chosen: ...widened (x1.25 a step) up to this when the "
                         "spheres would be more than the budget (handled_cooking_pot: 7.5 mm)")
CARRY_TILT = _t("CARRY_TILT", 0.15, "rad", "chosen, unmeasured: a held object may tilt from its start this much "
                "more than the move's goal itself does, on every move (kinematics.carry_tilt_allowed); a goal "
                "within it of the start keeps the load level (holds_level)")
CARRY_LOW_TOL = _t("CARRY_LOW_TOL", 0.01, "m", "inherited (the old 1 cm \"at a carry spot\"): a load's bottom may "
                   "sit this far below its carry floor")
CARRY_SUPPORT_Z = _t("CARRY_SUPPORT_Z", (0.3, 1.0), "m", "chosen, unmeasured: a destination's support height in "
                     "this band sets the carry height; floor-level or out-of-reach ones keep the default carry")
FLOOR_Z = _t("FLOOR_Z", 0.05, "m", "chosen: an object whose bottom is lower stands on the floor (the torso down)")

# --------------------------------------------------------------- the contact monitor (clearance, sticky)
MIN_DEPTH = _t("MIN_DEPTH", 0.003, "m", "chosen: a shallower penetration is the sphere model's noise")
MOVED_M = _t("MOVED_M", 0.02, "m", "chosen: an object nobody holds may drift this far between checks...")
MOVED_TILT = _t("MOVED_TILT", 20.0, "deg", "chosen: ...or its up axis tip this far (turning about it not counted)")
CARRIED_M = _t("CARRIED_M", 0.02, "m", "chosen: an object that moved like a held one since the last check, within "
               "this, rides in / on it")
APPROACH_MOVED_M = _t("APPROACH_MOVED_M", 0.001, "m", "measured: an object the motion must not touch counts as "
                      "moved past this (a fingertip knocking a mug on its rim: 4 mm, 2.8 deg, T04 no_cup 11-05; "
                      "untouched, the mug stood within 0.01 mm)")
APPROACH_TURN = _t("APPROACH_TURN", 1.0, "deg", "as APPROACH_MOVED_M, any axis")
SNAP_NEAR = _t("SNAP_NEAR", 0.30, "m", "chosen: sticky hands snap an object the hand is this close to where the "
               "hand is")

# --------------------------------------------------------------- what a skill's hooks judge (skill_jobs, skills)
SHUT = _t("SHUT", 0.003, "m", "chosen: fingers closer than this hold nothing between the pads (sticky, pick's "
          "after_close, _pick_judged)")
GRIP_CLOSED_BY = _t("GRIP_CLOSED_BY", 0.003, "m", "chosen: each finger closed at least this far from the opening "
                    "it was given met the object (a finger left at the opening touched nothing: [0.0102, 0.04] on "
                    "T13's mug, welded and carried as held)")
PICK_RISE_MIN = _t("PICK_RISE_MIN", 0.01, "m", "chosen: a hand that rose less after the close (a carry pose kept "
                   "where the arm stood) does not judge the lift")
PICK_LIFT_FRAC = _t("PICK_LIFT_FRAC", 0.5, "1", "chosen: the object rose more than this of the hand's rise: it "
                    "came along")
HELD_SLIP = _t("HELD_SLIP", 0.05, "m", "inherited, unmeasured: a load whose TCP distance changed more slipped "
               "(check_held, check_left_held, bimanual) -- the one bound on drift the code has; HOLD_DRIFT "
               "is still to measure")
HELD_SHIFT_MAX = _t("HELD_SHIFT_MAX", 0.08, "m", "inherited: ...up to this, still between the pads "
                    "(HELD_SHIFT_GAP), it shifted in the pinch and is re-anchored (check_held)")
HELD_SHIFT_GAP = _t("HELD_SHIFT_GAP", 0.008, "m", "inherited: the finger gap (sum) of a load still between the "
                    "pads")
HELD_LOST_GAP = _t("HELD_LOST_GAP", 0.004, "m", "inherited: a finger gap (sum) below this holds nothing (an "
                   "off-centre rim pinch drives one finger to ~0 while holding)")
PLACE_LEVEL_MIN = _t("PLACE_LEVEL_MIN", 5.0, "deg", "chosen: a held object tilted more than this is levelled for "
                     "the place")
PLACE_XY_TOL = _t("PLACE_XY_TOL", 0.10, "m", "chosen: a placed object this far (xy) off its spot, on the support, "
                  "is placed -- the task's tolerance, not the motion's (PLACE_TOL)")
PLACE_XY_TOL_CORNER = _t("PLACE_XY_TOL_CORNER", 0.12, "m", "chosen: ...a corner-held one (it pivots flat on "
                         "release)")
HANDLE_FINGER_MIN = _t("HANDLE_FINGER_MIN", (0.004, 0.3), "m, 1", "chosen: closed on a bar of thickness t, each "
                       "finger stopped at least min(0.004, 0.3 t) open (thin arched pulls: ~5 mm)")
HANDLE_GAP = _t("HANDLE_GAP", (0.6, 0.007, 0.03), "1, m, m", "chosen: ...and the finger gap (sum) within "
                "(max(0.6 t, t - 0.007), t + 0.03)")
HAND_OPENED_FRAC = _t("HAND_OPENED_FRAC", 0.5, "1", "chosen: both fingers open past this of the pre-open width: "
                      "the handle is let go")
DOOR_OPEN_TOL = _t("DOOR_OPEN_TOL", 0.10, "rad", "chosen: a hinge this close to its goal after the release is "
                   "open / closed")
DRAWER_OPEN_FRAC = _t("DRAWER_OPEN_FRAC", 0.4, "1", "chosen: a released drawer slides back a little: within this "
                      "of its travel (60 % open) is open")
DOOR_CLOSED_TOL = _t("DOOR_CLOSED_TOL", 0.04, "m", "= the evaluator's \"closed\" (a drawer closed: skills, old "
                     "close path)")
RIDE_DONE_REV = _t("RIDE_DONE_REV", 0.02, "rad", "inherited (skills._ride's): a ride's hinge this short of the "
                   "goal is there")
RIDE_DONE_PRIS = _t("RIDE_DONE_PRIS", 0.006, "m", "inherited: ...a slide")
RIDE_OVERSHOOT = _t("RIDE_OVERSHOOT", 0.02, "rad / m", "inherited (skills._ride's): the ride's script runs this "
                    "far past the goal (the ride commands up to it)")
PUSH_DONE_TOL = _t("PUSH_DONE_TOL", 0.01, "m", "inherited (skills' old push): an object pushed to within this of "
                   "the distance asked is there -- no further leg (skill_jobs.slide.push_object)")
PUSH_MOVED_MIN = _t("PUSH_MOVED_MIN", (0.01, 0.3), "m, 1", "inherited (skills' old push): a leg that moved the "
                    "object less than min(0.01, 0.3 of the leg) did not move it (a short top-up leg is mostly "
                    "approach: judged against its own length)")

TORSO_AT = _t("TORSO_AT", 0.02, "m", "inherited (policies/posture.py SetTorsoHeightPolicy), unmeasured: a torso lift "
               "this close to where a posture sent it got there (skill_jobs.posture body_job)")
WAIST_AT = _t("WAIST_AT", 0.035, "rad", "inherited (policies/posture.py SetWaistPitchPolicy), unmeasured: a waist "
               "pitch this close to where a posture sent it got there (skill_jobs.posture body_job)")

# --------------------------------------------------------------- the held, gesture and contact skills (HAND_PLAN 9e-9i)
# Moved here from skill_jobs with the rule audit of 11-25, values unchanged.  The task's own thresholds these skills'
# results share (lift's 2 cm, point's 8 deg, flip's z dot, wipe's coverage, knock's and touch's "did not move") are
# the predicates' (predicates.py); the goal sets the jobs sample (where a hand presents, rotates, waves, knocks ...)
# stay with the jobs (docs 2.3: the job's part is the goal sampling), registered in COLLISION_PLAN section 8.
HOVER_CLEAR = _t("HOVER_CLEAR", 0.06, "m", "inherited (the old HoverOverPolicy's clearance_m), unmeasured: a hover "
                 "holds the load's lowest point this far above the target's top -- inside the hovering_over "
                 "predicate's 0.03-0.15 m")
ROTATE_NEAR_BASE = _t("ROTATE_NEAR_BASE", 0.35, "m", "inherited (the old RotateHeldPolicy's), unmeasured: no staging "
                      "pose of a rotate is pulled closer to the base than this")
ROTATE_TOL_DEG = _t("ROTATE_TOL_DEG", 10.0, "deg", "inherited (the old RotateHeldPolicy's), unmeasured: the load's "
                    "yaw changed this close to the angle asked has turned (rotate's result)")
UPRIGHT_RAISE = _t("UPRIGHT_RAISE", 0.12, "m", "inherited (the old UprightObjectPolicy's raise), unmeasured: an upright "
                   "where the hand stands raises the TCP at least this (or half the load's longest side)")
WAVE_AMP = _t("WAVE_AMP", 0.10, "m", "inherited (the old WaveHandPolicy's), unmeasured: the raised hand swings this "
              "far to each side")
SHAKE_SLIP = _t("SHAKE_SLIP", 0.008, "m", "chosen, unmeasured (HAND_PLAN 9h): a pinch that closed more than this "
                "while shaking let the load turn in it (shake's result)")
FLIP_RELEASE = _t("FLIP_RELEASE", math.radians(105.0), "rad", "inherited (the old FlipFlatPolicy's release_deg), "
                  "unmeasured: a flip's arc goes this far at most")
FLIP_PAST = _t("FLIP_PAST", math.radians(95.0), "rad", "inherited (the old FlipFlatPolicy's PAST_VERTICAL_DEG), "
               "unmeasured: an arc this far is past vertical -- released short of it, the open hand pushes on")
FLIP_PUSH_TO = _t("FLIP_PUSH_TO", math.radians(120.0), "rad", "inherited (the old release + 15 deg), unmeasured: "
                  "the open hand's push along the arc ends here")
FLIP_MIN = _t("FLIP_MIN", math.radians(60.0), "rad", "inherited (the old FlipFlatPolicy's check), unmeasured: an arc "
              "shorter than this cannot turn it -- plan_flip's min_arc, at a park and in a rebuild")
POUR_TILT = _t("POUR_TILT", math.radians(110.0), "rad", "inherited (the old PourIntoPolicy's largest commanded tilt), "
               "unmeasured: a pour tilts this far at most")
POUR_MIN_TILT = _t("POUR_MIN_TILT", math.radians(60.0), "rad", "inherited (the old PourIntoPolicy's rocking "
                   "threshold: below it nothing poured), unmeasured: plan_pour's min_tilt, at a park and in a rebuild")
POUR_ABOVE = _t("POUR_ABOVE", 0.05, "m", "inherited (the old PourIntoPolicy's), unmeasured: the cup's bottom this "
                "far over the target's rim where the tilt starts")
WIPE_LENGTH = _t("WIPE_LENGTH", 0.30, "m", "inherited (the old WipeSurfacePolicy's): the strip wiped when the task "
                 "names no length")
WIPE_INSETS = _t("WIPE_INSETS", (0.08, 0.045), "m", "inherited (the old WipeSurfacePolicy's sampling): a strip runs "
                 "this far in from a support edge (the second where objects line the first)")
WIPE_ON = _t("WIPE_ON", 0.008, "m", "inherited (the old WipeSurfacePolicy's), unmeasured: the sponge's lowest point "
             "this close to the surface counts as pressed (the coverage samples)")
WIPE_CELL = _t("WIPE_CELL", 0.02, "m", "inherited (the old WipeSurfacePolicy's): a coverage cell of the strip")
HANDOVER_LONG = _t("HANDOVER_LONG", 0.15, "m", "inherited (the old HandoverRightToLeftPolicy's), unmeasured: a load "
                   "whose longest side is over this is handed over turned across the body (skill_jobs.pick "
                   "HANDOVER_AXIS)")
POINT_FRONT = _t("POINT_FRONT", 0.2, "1", "chosen (HAND_PLAN 9h): a point's ray from the hand's shoulder to "
                  "the target runs at least this forward (its unit vector's forward part): in front -- the one test "
                  "the point skill refuses by and the task layer turns the robot by (skill_jobs.held.point_in_front)")
TIP_PAST = _t("TIP_PAST", 0.03, "m", "chosen, unmeasured (HAND_PLAN 9h): a tip's poke runs this far past the length "
              "the object lies down over (twice its half-size along the push)")

# --------------------------------------------------------------- the execution's arrived / stalled (rig)
SETTLE_TCP = _t("SETTLE_TCP", 0.001, "m", "measured: a follow has arrived with the TCP this close to where q_cmd "
                "puts it -- a fifth of TARGET_TOL; settled reaches err 0.1-0.4 mm (pick612_verify)")
SETTLE_STILL = _t("SETTLE_STILL", 0.002, "m/s", "chosen: ...or stopped, the TCP slower than this over "
                  "SETTLE_WINDOW (blocked, or held off by the drives' steady error); a hand closing a 5 mm error "
                  "moves 10+ mm/s")
RIDE_STALL = _t("RIDE_STALL", 0.003, "rad / m", "inherited (skills._ride's): a part that moved less between two "
                "checks, RIDE_STALL_CHECKS in a row, has stalled")
RIDE_SLIP_LEADS = _t("RIDE_SLIP_LEADS", 2.0, "leads", "not measured: a part this many leads behind a ride's "
                     "command dropped back, it slipped (a part that follows lags at most lead + rate / PHYSICS_HZ "
                     "by construction)")
EDGE_PAD_CLEAR = _t("EDGE_PAD_CLEAR", 0.005, "m", "chosen: an edge hold's open pads keep this from the load once "
                    "it landed, before they pull out (skill_plans.place_clear) -- a straight's check itself has no "
                    "margin (cuRobo's collision constraint: activation distance 0)")
HEAD_AT = _t("HEAD_AT", 0.02, "rad", "inherited (the old policies.perceive.drive_head's, now Rig.aim_head): a head joint this close to its "
             "command has arrived; run_skill leaves a head this close to straight ahead where it is")

# --------------------------------------------------------------- what an exploration counts (policies.perceive, 9.3 step 3)
COVER_MIN_AREA = _t("COVER_MIN_AREA", 0.05, "m^2", "inherited (5df416bf), unmeasured: a support smaller than this is "
                    "not a room-coverage target (explore_room)")
COVER_Z = _t("COVER_Z", (0.3, 1.6), "m", "inherited (5df416bf), unmeasured: support layers between these heights are "
             "the horizontal surfaces in sight a room exploration must see")
COVER_MIN_CLEARANCE = _t("COVER_MIN_CLEARANCE", 0.3, "m", "inherited (5df416bf), unmeasured: ...with at least this "
                         "much free height above them")
COVER_OK = _t("COVER_OK", 0.75, "1", "inherited (5df416bf), unmeasured: the fraction of its targets a room "
              "exploration must see to succeed")
VIEW_TURNS = _t("VIEW_TURNS", (0.0, 180.0), "deg", "inherited (5df416bf), unmeasured: the base headings, relative to "
                "where it arrived, a room viewpoint sweeps from (look both ways)")
SWEEP_YAWS = _t("SWEEP_YAWS", (-1.0, -0.5, 0.0, 0.5, 1.0), "rad", "inherited (5df416bf), unmeasured: the head yaws of "
                "a room sweep...")
SWEEP_PITCH = _t("SWEEP_PITCH", 0.3, "rad", "inherited (5df416bf), unmeasured: ...at this pitch (positive looks down)...")
SWEEP_STEPS = _t("SWEEP_STEPS", 50, "ticks", "inherited (5df416bf), unmeasured: ...each reached in this many ticks")
LOOK_STEPS = _t("LOOK_STEPS", 90, "ticks", "inherited (drive_head's default), unmeasured: a head segment aimed at a "
                "point arrives in this many ticks at most")
SEARCH_STEPS = _t("SEARCH_STEPS", 60, "ticks", "inherited (search's drive_head), unmeasured: ...one of search's")
SEARCH_AIM_SPACING_M = _t("SEARCH_AIM_SPACING_M", 0.6, "m", "chosen (5e962d8f): search aims the head at points this far "
                          "apart along a long support (one look at the centre of counter_2, 2.47 m long, left a pot "
                          "at its end 52 deg off the axis)")
COUNT_YAWS = _t("COUNT_YAWS", (-0.9, -0.3, 0.3, 0.9), "rad", "inherited (extra.CountCategoryPolicy's), unmeasured: "
                "the head yaws count looks along, at pitch 0.25 rad")

# --------------------------------------------------------------- visual prompting for place (visual_prompt: mark_spots, view_support)
SPOT_NEAR = _t("SPOT_NEAR", 0.15, "m", "chosen (11-16, the v6 near_any goals' 15 cm): an object is near a spot when the "
               "held object put there (a square of its longer side) leaves at most this gap to its footprint; the spots "
               "cover every set of near objects a free spot has (user 11-17: one spot for each case of each object "
               "within / not within 15 cm, none where nothing fits)")
MAX_SPOTS = _t("MAX_SPOTS", 16, "1", "chosen (11-17): spots numbered over the images at most -- one for each set of "
               "near objects and no more (a dining table with three seats has about a dozen; 12 on 11-16, 6 before)")
SPOT_SET_SEP = _t("SPOT_SET_SEP", 0.06, "m", "chosen (11-17): two spots at least this far apart (the discs kept apart on "
                  "the image by SPOT_PX_SEP): at 12 cm, 11-17 T01's crowded seats had 9 of their 18 sets left without "
                  "a spot, the bowl-and-mug one among them")
SPOT_PX_SEP = _t("SPOT_PX_SEP", 2.4, "disc radii", "chosen (11-16): two discs' centres at least this many radii apart "
                 "on the image (11-15 T01: two discs drawn one over the other at the far end of the table)")
SPOT_CELL = _t("SPOT_CELL", 0.06, "m", "chosen (11-15): the open-space spots come from free spots thinned to one per "
               "cell this wide (free_spots' best sit in the corner nearest the robot: 11-15 T20)")
SPOT_EDGE_FRAC = _t("SPOT_EDGE_FRAC", 0.04, "image width", "chosen (11-15): a spot this close to the image border is "
                    "not drawn")
VIEW_GRID_N = _t("VIEW_GRID_N", 5, "1", "chosen (11-15): samples per side of a support's top a view is judged on "
                 "(corners included)")
VIEW_FRUSTUM_MARGIN = _t("VIEW_FRUSTUM_MARGIN", 0.92, "1", "chosen (11-15): a sample is in view inside this fraction "
                         "of the frustum's half-angle tangents (a corner on the border is half cut off)")
VIEW_AIM_FRACS = _t("VIEW_AIM_FRACS", (0.5, 0.3, 0.7), "1", "chosen (11-15): the head aims at the support's centre or "
                    "nearer / farther along the view line by this fraction of its half-diagonal")
VIEW_RES_MIN = _t("VIEW_RES_MIN", 0.15, "half image widths / m", "chosen (11-16): a sample of a support's top counts "
                  "as seen when a view resolves it at least this finely (visual_prompt.resolution: with the camera "
                  "0.3 m above a table, within about 1.9 m; 11-16 T21: a spot 2.9 m off at 0.09 looked next to the "
                  "kid's cup and was 29 cm from it)")
VIEW_MAX = _t("VIEW_MAX", 2, "1", "chosen (11-16, the user: two images): view_support takes at most this many views of "
              "one support (a long table: one per half)")
VIEW_MIN_GAIN = _t("VIEW_MIN_GAIN", 0.2, "1", "chosen (11-16): a further view is taken only when it sees at least this "
                   "fraction of the support's samples no view so far has seen")
VIEW_KEEP_FRAC = _t("VIEW_KEEP_FRAC", 0.8, "1", "chosen (11-16): the first view is taken where the robot stands when "
                    "that sees at least this fraction of what the best first view would (no drive for a little more)")
