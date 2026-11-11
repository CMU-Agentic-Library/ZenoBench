"""The thresholds of the motion layers' error model, one source each (docs/MOTION_ARCHITECTURE.md
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
uses them."""

from __future__ import annotations

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
TARGET_TOL = _t("TARGET_TOL", 0.005, "m", "chosen: a hand stopped this far short of where it was sent is "
                "blocked (pick's after_grasp, place's after_down; until 11-11 also named skills.PICK_REACH_TOL): reach "
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
CARRY_TILT = _t("CARRY_TILT", 0.15, "rad", "chosen, unmeasured: largest tilt of a held object from its start "
                "orientation on a planned move")
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
