---
name: rotate-object
description: Turn the held object about the vertical axis by the requested angle (e.g. align a book's spine).
---

# Rotate a held object (`rotate`)

`rotate(object: object_ref, degrees: number)`

Turn the held object about the vertical axis by the requested angle (e.g. align a book's spine).

## When to use

A held object must turn about the vertical axis (align a handle or label).

## Not to be confused with

- `flip`: flip turns an object upside down; rotate keeps it level.

## Inputs

- `object` (`object_ref`): The held object.
- `degrees` (`number`): Yaw change in degrees (positive = counter-clockwise).

## Call

Send one JSON object:

```json
{"contract": "rotate", "args": {"object": "<object>", "degrees": "<number>"}}
```

Argument formats:

- `number`: a finite number
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

- `yaw_rotated(object=$object, degrees=$degrees)` — Object yaw changed by the requested angle within 10 deg.
- `holding(hand=right, object=$object)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

