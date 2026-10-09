---
name: lower-object
description: Move the held object down until its bottom is at most the given height (e.g. under a low shelf clearance).
---

# Lower a held object (`lower`)

`lower(object: object_ref, height_m: positive_number)`

Move the held object down until its bottom is at most the given height (e.g. under a low shelf clearance).

## When to use

A held object must be brought down to a height without releasing it.

## Not to be confused with

- `place`: lower keeps holding the object.

## Inputs

- `object` (`object_ref`): The held object.
- `height_m` (`positive_number`): Maximum world height of the object's bottom.

## Call

Send one JSON object:

```json
{"contract": "lower", "args": {"object": "<object>", "height_m": "<positive_number>"}}
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

- `held_below(object=$object, height_m=$height_m)` — Right-held object's bottom at or below the given world height (2 cm tolerance).
- `holding(hand=right, object=$object)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.

## May invalidate

`held_above($object,*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

