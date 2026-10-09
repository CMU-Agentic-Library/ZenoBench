---
name: expose-object
description: Push a flat object (book, plate, notebook) until it overhangs a free support edge by >= 5.5 cm while its centre of mass stays on the support, so the overhang can be pinched.
---

# Expose a grasp edge (`expose`)

`expose(object: object_ref)`

Push a flat object (book, plate, notebook) until it overhangs a free support edge by >= 5.5 cm while its centre of mass stays on the support, so the overhang can be pinched.

## When to use

A flat object is wider than the gripper and must overhang an edge before pick.

## Not to be confused with

- `push`: expose pushes toward a free edge until a pinchable overhang exists.

## Inputs

- `object` (`object_ref`): A flat object on a support.

## Call

Send one JSON object:

```json
{"contract": "expose", "args": {"object": "<object>"}}
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

- `edge_overhang(object=$object)` — A flat object overhangs a support edge enough for an edge pinch (>= 5.5 cm) while its centre of mass stays 3.5 cm inside the edge.

## May invalidate

`at_initial_place($object)`, `away_from_edge($object,*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

