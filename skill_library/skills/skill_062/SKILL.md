---
name: shake-object
description: Oscillate the held object sideways three times (settle or loosen contents) while keeping the grasp.
---

# Shake a held object (`shake`)

`shake(object: object_ref)`

Oscillate the held object sideways three times (settle or loosen contents) while keeping the grasp.

## When to use

The grasp must be tested or contents shaken while holding.

## Not to be confused with

- `stir`: stir moves a utensil inside a container; shake moves the held object itself.

## Inputs

- `object` (`object_ref`): The right-held object.

## Call

Send one JSON object:

```json
{"contract": "shake", "args": {"object": "<object>"}}
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

Requires holding(hand=right, object=$object).

## Preconditions (checked before moving)

- `holding(hand=right, object=$object)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.

## Postconditions (checked after the action)

- `shaken(object=$object)` — The held object was oscillated at least three times with >= 2 cm amplitude without slipping.
- `holding(hand=right, object=$object)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

