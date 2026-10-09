---
name: square-object
description: Align an object's edges with its support's edges (yaw within 5 deg): pick it, turn it by the measured yaw error and set it back down at the same spot.
---

# Square an object (`square`)

`square(object: object_ref)`

Align an object's edges with its support's edges (yaw within 5 deg): pick it, turn it by the measured yaw error and set it back down at the same spot.

## When to use

An object must be rotated so its sides align with the support edges.

## Not to be confused with

- `rotate`: rotate turns a held object by a requested angle; square finds the angle itself.

## Inputs

- `object` (`object_ref`): An object resting on a support.

## Call

Send one JSON object:

```json
{"contract": "square", "args": {"object": "<object>"}}
```

Argument formats:

- `object_ref`: a movable annotated scene object

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires hand_empty(hand=right); base_near(place=$object).

## Preconditions (checked before moving)

- `hand_empty(hand=right)` — The given gripper holds nothing.
- `base_near(place=$object)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).

## Postconditions (checked after the action)

- `squared(object=$object)` — Object yaw within 5 deg of the support's axes (edges parallel), resting on a support.
- `hand_empty(hand=right)` — The given gripper holds nothing.

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

