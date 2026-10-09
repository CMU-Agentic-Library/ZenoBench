---
name: brace-object
description: Pinch a resting container with the left gripper so it cannot slide while the right hand stirs, wipes or pours into it.
---

# Brace an object with the left hand (`brace`)

`brace(object: object_ref)`

Pinch a resting container with the left gripper so it cannot slide while the right hand stirs, wipes or pours into it.

## When to use

An object must be held still by the left hand while the right hand works on it.

## Not to be confused with

- `pick`: brace leaves the object on its support.

## Inputs

- `object` (`object_ref`): The resting object to hold still.

## Call

Send one JSON object:

```json
{"contract": "brace", "args": {"object": "<object>"}}
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

Requires hand_empty(hand=left); base_near(place=$object).

## Preconditions (checked before moving)

- `hand_empty(hand=left)` — The given gripper holds nothing.
- `base_near(place=$object)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).

## Postconditions (checked after the action)

- `steadied(object=$object)` — The left gripper pinches the object while it still rests on its support.
- `holding(hand=left, object=$object)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.

## May invalidate

`arm_stowed(left)`, `hand_empty(left)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

