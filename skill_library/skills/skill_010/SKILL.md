---
name: reset-posture
description: Return to the home posture: fingers open, arm folded, torso up, waist straight, by a collision-checked joint-space move. Used to recover from an unknown arm state.
---

# Reset the posture (`reset`)

`reset()`

Return to the home posture: fingers open, arm folded, torso up, waist straight, by a collision-checked joint-space move. Used to recover from an unknown arm state.

## When to use

Start or end of a task, or after a failure, to return to a known posture.

## Not to be confused with

- `tuck`: tuck only folds one arm; reset also restores torso and waist.

## Inputs

- none

## Call

Send one JSON object:

```json
{"contract": "reset", "args": {}}
```

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires hand_empty(hand=right).

## Preconditions (checked before moving)

- `hand_empty(hand=right)` — The given gripper holds nothing.

## Postconditions (checked after the action)

- `arm_stowed(hand=right)` — The arm is folded at its travel posture.
- `torso_raised()` — Torso lift within 3 cm of its highest position (travel height).
- `waist_straight()` — Waist pitch within 0.05 rad of upright.

## May invalidate

`torso_lowered()`, `waist_bent(*)`, `reachable(*)`, `pointing_at(*)`, `in_view(*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

