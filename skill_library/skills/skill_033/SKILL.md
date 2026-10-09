---
name: center-object
description: Push an object back from the support edges until every edge margin is at least the requested value (secures an item left overhanging).
---

# Center an object on its support (`center`)

`center(object: object_ref, margin_m: positive_number)`

Push an object back from the support edges until every edge margin is at least the requested value (secures an item left overhanging).

## When to use

An object near a support edge must be moved inward so it cannot fall.

## Not to be confused with

- `push`: center moves the object away from the nearest edge by a margin.

## Inputs

- `object` (`object_ref`): The object near an edge.
- `margin_m` (`positive_number`, default 0.06): Required margin to every edge.

## Call

Send one JSON object:

```json
{"contract": "center", "args": {"object": "<object>", "margin_m": "<positive_number>"}}
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

- `away_from_edge(object=$object, margin_m=$margin_m)` — Object footprint at least the margin inside every edge of its support.

## May invalidate

`edge_overhang($object)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

