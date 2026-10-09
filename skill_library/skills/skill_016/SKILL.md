---
name: present-object
description: Hold the carried object in front of the body at 0.9-1.4 m height, inside the head camera view.
---

# Present a held object (`present`)

`present(object: object_ref)`

Hold the carried object in front of the body at 0.9-1.4 m height, inside the head camera view.

## When to use

A held object must be shown to the head camera or a person.

## Not to be confused with

- `lift`: lift only changes the height; present holds the object in front of the head.

## Inputs

- `object` (`object_ref`): The right-held object to show.

## Call

Send one JSON object:

```json
{"contract": "present", "args": {"object": "<object>"}}
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

- `presenting(object=$object)` — The right-held object is in front of the body at 0.9-1.4 m height and in the head camera view.
- `holding(hand=right, object=$object)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.

## May invalidate

`reachable(*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

