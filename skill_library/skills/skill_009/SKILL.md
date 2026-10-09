---
name: tuck-arm
description: Fold an empty arm to its travel posture along a collision-checked path.
---

# Tuck an arm (`tuck`)

`tuck(hand: hand)`

Fold an empty arm to its travel posture along a collision-checked path.

## When to use

Before driving through a narrow passage or after a hand action left the arm out.

## Not to be confused with

- `reset`: reset also restores torso, waist and head; tuck only folds the arm.

## Inputs

- `hand` (`hand`, one of 'right', 'left', default 'right'): Which arm to fold.

## Call

Send one JSON object:

```json
{"contract": "tuck", "args": {"hand": "<hand>"}}
```

Argument formats:

- `hand`: "right" or "left"

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires hand_empty(hand=$hand).

## Preconditions (checked before moving)

- `hand_empty(hand=$hand)` — The given gripper holds nothing.

## Postconditions (checked after the action)

- `arm_stowed(hand=$hand)` — The arm is folded at its travel posture.

## May invalidate

`reachable(*)`, `pointing_at(*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

