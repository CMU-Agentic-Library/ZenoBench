---
name: lift-object
description: Raise the held object until its bottom is at least the given world height (e.g. above a bin rim or a furniture edge before carrying).
---

# Lift a held object (`lift`)

`lift(object: object_ref, height_m: positive_number)`

Raise the held object until its bottom is at least the given world height (e.g. above a bin rim or a furniture edge before carrying).

## When to use

A held object must be raised to a height (clear an obstacle, show it).

## Not to be confused with

- `stand`: stand moves the torso, not the held object.
- `lower`: opposite direction.
- `pick`: lift raises an object already held.

## Inputs

- `object` (`object_ref`): The held object.
- `height_m` (`positive_number`, default 0.55): Minimum world height of the object's bottom.

## Call

Send one JSON object:

```json
{"contract": "lift", "args": {"object": "<object>", "height_m": "<positive_number>"}}
```

Argument formats:

- `object_ref`: a movable annotated scene object
- `positive_number`: a number > 0

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires holding(hand=right, object=$object).

## Preconditions (checked before moving)

- `holding(hand=right, object=$object)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.

## Postconditions (checked after the action)

- `held_above(object=$object, height_m=$height_m)` — Right-held object's bottom at or above the given world height (2 cm tolerance).
- `holding(hand=right, object=$object)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.

## May invalidate

`held_below($object,*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

