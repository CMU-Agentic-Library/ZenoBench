---
name: push-object
description: Slide an object along its support in a direction with closed fingers: from behind when there is room, or by pressing on its top and dragging when it stands against a wall or closed edge.
---

# Push an object (`push`)

`push(object: object_ref, direction_xy: unit_vec2, distance_m: positive_number)`

Slide an object along its support in a direction with closed fingers: from behind when there is room, or by pressing on its top and dragging when it stands against a wall or closed edge.

## When to use

An object must slide along its support without grasping it.

## Not to be confused with

- `pull`: pull drags toward the base to make an object reachable.
- `expose`: expose pushes until a graspable overhang exists.
- `separate`: separate pushes away from the nearest neighbour.
- `center`: center pushes away from the support edges.
- `roll`: roll makes a cylinder rotate instead of slide.
- `tip`: tip pushes high so the object falls over.
- `sweep`: sweep gathers several objects.

## Inputs

- `object` (`object_ref`): The object to slide.
- `direction_xy` (`unit_vec2`): World horizontal direction.
- `distance_m` (`positive_number`): Requested travel.

## Outputs

- `moved_m` (`number`): Measured displacement along the direction.

## Call

Send one JSON object:

```json
{"contract": "push", "args": {"object": "<object>", "direction_xy": "<unit_vec2>", "distance_m": "<positive_number>"}}
```

Argument formats:

- `object_ref`: a movable annotated scene object
- `positive_number`: a number > 0
- `unit_vec2`: a horizontal unit vector [x, y]

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

- `object_moved(object=$object, direction_xy=$direction_xy, distance_m=$distance_m)` — Object displaced along the direction by at least half the requested distance.

## May invalidate

`edge_overhang($object)`, `grasp_clearance($object)`, `away_from_edge($object,*)`, `at_initial_place($object)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

