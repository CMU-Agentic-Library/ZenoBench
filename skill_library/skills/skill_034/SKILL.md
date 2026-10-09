---
name: roll-object
description: Roll a lying constant-radius cylinder (rolling pin, can on its side) along its support by pressing on its top; the object must rotate, not slide. A bottle with a neck rolls in an arc around the neck and is not a valid noun.
---

# Roll a cylinder (`roll`)

`roll(object: object_ref, distance_m: positive_number)`

Roll a lying constant-radius cylinder (rolling pin, can on its side) along its support by pressing on its top; the object must rotate, not slide. A bottle with a neck rolls in an arc around the neck and is not a valid noun.

## When to use

A lying cylinder must move along the support by rotating.

## Not to be confused with

- `push`: push slides the object; roll makes it rotate.

## Inputs

- `object` (`object_ref`): A lying cylinder.
- `distance_m` (`positive_number`, default 0.1): Requested travel.

## Call

Send one JSON object:

```json
{"contract": "roll", "args": {"object": "<object>", "distance_m": "<positive_number>"}}
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

Requires hand_empty(hand=right); base_near(place=$object); lying(object=$object).

## Preconditions (checked before moving)

- `hand_empty(hand=right)` — The given gripper holds nothing.
- `base_near(place=$object)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).
- `lying(object=$object)` — Object on its side: longest axis within 60 deg of horizontal and vertical extent <= 60 % of its length.

## Postconditions (checked after the action)

- `object_rolled(object=$object)` — Object rotated at least 45 deg about a horizontal axis while staying on its side.

## May invalidate

`at_initial_place($object)`, `grasp_clearance($object)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

