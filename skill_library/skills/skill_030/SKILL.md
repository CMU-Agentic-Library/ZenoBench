---
name: pull-object
description: Drag an object toward the robot with the pads pressed on its top until it is within reach (e.g. from the back of a deep counter); if the pads slide over a round or slippery top, the fingers hook the far side and push it toward the robot.
---

# Pull an object closer (`pull`)

`pull(object: object_ref, distance_m: positive_number)`

Drag an object toward the robot with the pads pressed on its top until it is within reach (e.g. from the back of a deep counter); if the pads slide over a round or slippery top, the fingers hook the far side and push it toward the robot.

## When to use

An object is too far back on a deep support to grasp and must come closer.

## Not to be confused with

- `push`: push moves the object away from the robot or sideways.

## Inputs

- `object` (`object_ref`): The object to drag.
- `distance_m` (`positive_number`, default 0.15): Requested travel toward the base.

## Call

Send one JSON object:

```json
{"contract": "pull", "args": {"object": "<object>", "distance_m": "<positive_number>"}}
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

Requires hand_empty(hand=right); base_near(place=$object).

## Preconditions (checked before moving)

- `hand_empty(hand=right)` — The given gripper holds nothing.
- `base_near(place=$object)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).

## Postconditions (checked after the action)

- `moved_toward_base(object=$object, distance_m=$distance_m)` — Object's horizontal distance to the base decreased by at least half the requested distance.
- `reachable(target=$object)` — From the current base pose the right TCP has a collision-free IK solution 10 cm above the target (handle pre-grasp for doors, 8 cm in front of a button).

## May invalidate

`grasp_clearance($object)`, `at_initial_place($object)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

