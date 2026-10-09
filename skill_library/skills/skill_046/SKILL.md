---
name: uncover-container
description: Lift the lid off a container by its knob and set it down beside the container: on the same support when it has room, else on the nearest counter-height support; the lid noun is found from GT (the lid resting on the rim).
---

# Uncover a container (`uncover`)

`uncover(container: container_ref)`

Lift the lid off a container by its knob and set it down beside the container: on the same support when it has room, else on the nearest counter-height support; the lid noun is found from GT (the lid resting on the rim).

## When to use

A lid must be removed before reaching into or pouring into a container.

## Not to be confused with

- `pick`: uncover also puts the lid aside.

## Inputs

- `container` (`container_ref`): The covered container.

## Outputs

- `lid` (`lid_ref`): The lid that was removed.

## Call

Send one JSON object:

```json
{"contract": "uncover", "args": {"container": "<container>"}}
```

Argument formats:

- `container_ref`: an object annotated as an open container

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires hand_empty(hand=right); base_near(place=$container).

## Preconditions (checked before moving)

- `hand_empty(hand=right)` — The given gripper holds nothing.
- `base_near(place=$container)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).

## Postconditions (checked after the action)

- `uncovered(container=$container)` — No lid rests on the container rim.
- `hand_empty(hand=right)` — The given gripper holds nothing.

## Conditions that depend on the bound nouns

- when container.lid: ensures `on(object=@container.lid, support=@container.aside_support)`

## May invalidate

`covered($container,*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

