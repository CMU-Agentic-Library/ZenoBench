---
name: separate-object
description: Push an object straight away from its closest neighbour until there is room for a finger (>= 3.5 cm gap) without leaving the support.
---

# Separate an object from its neighbour (`separate`)

`separate(object: object_ref)`

Push an object straight away from its closest neighbour until there is room for a finger (>= 3.5 cm gap) without leaving the support.

## When to use

Two objects are too close for the fingers to fit beside one of them.

## Not to be confused with

- `push`: separate pushes until a finger fits beside the object.

## Inputs

- `object` (`object_ref`): The crowded object.

## Call

Send one JSON object:

```json
{"contract": "separate", "args": {"object": "<object>"}}
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

- `grasp_clearance(object=$object)` — Some annotated pinch of the object has both finger slots (2.8 x 1.2 cm, at the pre-grasp opening) free of neighbours; objects without a pinch need 3.5 cm of free footprint gap.

## May invalidate

`at_initial_place($object)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

