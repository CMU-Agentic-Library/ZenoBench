---
name: stack-object
description: Set the held object centred on the top face of another object (block on block, plate on plate).
---

# Stack an object on another (`stack`)

`stack(object: object_ref, base: object_ref)`

Set the held object centred on the top face of another object (block on block, plate on plate).

## When to use

A held object must be put on top of another object.

## Not to be confused with

- `place`: place targets a support or container; stack targets the top face of an object.

## Inputs

- `object` (`object_ref`): The held object.
- `base` (`object_ref`): The object to stack onto.

## Call

Send one JSON object:

```json
{"contract": "stack", "args": {"object": "<object>", "base": "<object>"}}
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

Requires holding(hand=right, object=$object); base_near(place=$base); top_clear(object=$base).

## Preconditions (checked before moving)

- `holding(hand=right, object=$object)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.
- `base_near(place=$base)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).
- `top_clear(object=$base)` — No other object rests on the object's top face.

## Postconditions (checked after the action)

- `on_top_of(object=$object, base=$base)` — Object rests on the base object's top face: bottom within 2 cm of it, centre over its footprint.
- `hand_empty(hand=right)` — The given gripper holds nothing.

## May invalidate

`holding(right,$object)`, `top_clear($base)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

