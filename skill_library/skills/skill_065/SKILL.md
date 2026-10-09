---
name: touch-object
description: Bring the closed fingertips onto an object's top and back off without moving it (probe / indicate by contact).
---

# Touch an object (`touch`)

`touch(object: object_ref)`

Bring the closed fingertips onto an object's top and back off without moving it (probe / indicate by contact).

## When to use

An object must be touched lightly (tap, confirm contact) without moving it.

## Not to be confused with

- `push`: push moves the object; touch must not.
- `press`: press actuates a button.

## Inputs

- `object` (`object_ref`): The object to touch.

## Call

Send one JSON object:

```json
{"contract": "touch", "args": {"object": "<object>"}}
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

- `touched(object=$object)` — A measured fingertip contact with the object's top during the Contract; it moved < 1.5 cm.
- `hand_empty(hand=right)` — The given gripper holds nothing.

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

