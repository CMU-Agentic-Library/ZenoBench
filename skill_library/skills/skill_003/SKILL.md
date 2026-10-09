---
name: face-target
description: Rotate the base in place until it faces the target (heading error <= 20 deg).
---

# Face a target (`face`)

`face(target: entity_ref)`

Rotate the base in place until it faces the target (heading error <= 20 deg).

## When to use

The target is beside or behind the robot and only the heading must change.

## Not to be confused with

- `look`: look moves the head only; face moves the whole base.

## Inputs

- `target` (`entity_ref`): What to face.

## Outputs

- `base_yaw_deg` (`number`): Measured heading after the turn.

## Call

Send one JSON object:

```json
{"contract": "face", "args": {"target": "<entity>"}}
```

Argument formats:

- `entity_ref`: any annotated object, support, articulated part or button

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

No precondition.

## Preconditions (checked before moving)

- none

## Postconditions (checked after the action)

- `facing(target=$target)` — Base heading within 20 deg of the target bearing.

## May invalidate

`reachable(*)`, `in_view(*)`, `pointing_at(*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

- turning in place would hit furniture
