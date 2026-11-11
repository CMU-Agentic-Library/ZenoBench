"""The thresholds of the motion layers' error model, one source each (docs/MOTION_ARCHITECTURE.md
4.5): the error bounds of the anchors (8.2), what a segment is checked again by (8.4), and the
contact geometry the primitives measure by (5.1-5.3).  Each with its unit and where its value comes
from (``src``) -- measured, estimated, chosen, or inherited and never measured -- so which numbers
stand on data can be read here, not dug out of four files.  The modules that use them import them
from here (primitives re-exports its own: code and tests that read ``primitives.TARGET_TOL`` keep
working).  Leaf module: imports nothing of zeno_skills.

What sets the open ones: 9.3 step 2.1, the anchors' and segments' logs (run.py: anchor ``off``,
segment ``aim_off``; skill_jobs.pick ``held_offset``) aggregated by tools/anchor_stats.py.

Not here: execution parameters (speeds, smooth, steps_per_wp: Segment.info), search budgets and
costs (park_search, skills), and the old code's thresholds (rig, skills, policies) -- those go
with the migration of what uses them."""

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
                   "command to command (q_cmd), the slack only numerical")
EXTENT_TOL = _t("EXTENT_TOL", LEAVE_MARGIN / 2, "m", "reasoned: a contact exit measured again within this "
                "still clears with half the margin (one 2 mm step was the measure's own resolution: 7 of 13 "
                "rebuilds of the 11-08 run)")
TARGET_TOL = _t("TARGET_TOL", 0.005, "m", "chosen: a hand stopped this far short of where it was sent is "
                "blocked (skills.PICK_REACH_TOL); unmeasured")
TARGET_TURN = _t("TARGET_TURN", HINT_TURN, "rad", "= HINT_TURN")
PICK_TOL = _t("PICK_TOL", (HINT_REACH, HINT_TURN), "m, rad", "chosen = decide_ik's: a pick's contact segments "
              "further off the grasp than built by more are rebuilt (a chain of fine motions on it); "
              "unmeasured -- anchor_stats 2 (pick_reach / pick_grasp aim_off)")
PLACE_TOL = _t("PLACE_TOL", (TARGET_TOL, TARGET_TURN), "m, rad", "chosen = TARGET_TOL: a set-down less off "
               "only sets the load down a few mm off; unmeasured -- anchor_stats 2 (place_reach / place_down)")
DOOR_TOL = _t("DOOR_TOL", (HINT_REACH, HINT_TURN), "m, rad", "chosen as PICK_TOL (the hook onto a bar is a "
              "fine motion); no sim run yet")
