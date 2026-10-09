---
name: point-target
description: Point the closed right fingers at a target (finger axis within 8 deg) to indicate it.
---

# Point at a target (`point`)

`point(target: entity_ref)`

Point the closed right fingers at a target (finger axis within 8 deg) to indicate it.

## When to use

A person must be shown an object or place without touching it.

## Not to be confused with

- `touch`: point does not make contact.

## Inputs

- `target` (`entity_ref`): What to indicate.

## Call

Send one JSON object:

```json
{"contract": "point", "args": {"target": "<entity>"}}
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

Requires hand_empty(hand=right).

## Preconditions (checked before moving)

- `hand_empty(hand=right)` — The given gripper holds nothing.

## Postconditions (checked after the action)

- `pointing_at(target=$target)` — The right finger axis points at the target within 8 deg.
- `hand_empty(hand=right)` — The given gripper holds nothing.

## May invalidate

`arm_stowed(right)`, `reachable(*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

