---
name: sweep-objects
description: Push several objects on one support toward their centroid until they form a cluster (radius 12 cm), without grasping them.
---

# Sweep objects together (`sweep`)

`sweep(objects: object_list, radius_m: positive_number)`

Push several objects on one support toward their centroid until they form a cluster (radius 12 cm), without grasping them.

## When to use

Several small objects on one support must be gathered into a cluster.

## Not to be confused with

- `arrange`: arrange picks and places; sweep only pushes.
- `collect`: collect puts objects into a container.

## Inputs

- `objects` (`object_list`): Objects on one support.
- `radius_m` (`positive_number`, default 0.12): Cluster radius.

## Call

Send one JSON object:

```json
{"contract": "sweep", "args": {"objects": "<object_list>", "radius_m": "<positive_number>"}}
```

Argument formats:

- `object_list`: a non-empty list of object refs
- `positive_number`: a number > 0

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires hand_empty(hand=right).

## Preconditions (checked before moving)

- `hand_empty(hand=right)` — The given gripper holds nothing.

## Postconditions (checked after the action)

- `clustered(objects=$objects, radius_m=$radius_m)` — Every listed object's footprint centre lies within the radius of the group centroid, on one support.

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

