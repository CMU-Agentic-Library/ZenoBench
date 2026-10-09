---
name: cover-container
description: Lay the held lid centred on the container rim (within 3 cm, tilt <= 12 deg) and release it.
---

# Cover a container with a lid (`cover`)

`cover(container: container_ref, lid: lid_ref)`

Lay the held lid centred on the container rim (within 3 cm, tilt <= 12 deg) and release it.

## When to use

A container must be closed with its lid.

## Not to be confused with

- `uncover`: opposite direction.
- `place`: cover rests the lid on the rim.

## Inputs

- `container` (`container_ref`): The pot or box to cover.
- `lid` (`lid_ref`): The held lid.

## Call

Send one JSON object:

```json
{"contract": "cover", "args": {"container": "<container>", "lid": "<lid>"}}
```

Argument formats:

- `container_ref`: an object annotated as an open container
- `lid_ref`: an object tagged as a lid

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires holding(hand=right, object=$lid); base_near(place=$container); uncovered(container=$container).

## Preconditions (checked before moving)

- `holding(hand=right, object=$lid)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.
- `base_near(place=$container)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).
- `uncovered(container=$container)` — No lid rests on the container rim.

## Postconditions (checked after the action)

- `covered(container=$container, lid=$lid)` — The lid rests centred on the container rim (3 cm xy, 3 cm height, 12 deg tilt).
- `hand_empty(hand=right)` — The given gripper holds nothing.

## May invalidate

`uncovered($container)`, `holding(right,$lid)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

