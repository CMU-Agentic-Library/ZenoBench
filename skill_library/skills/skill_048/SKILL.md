---
name: collect-objects
description: Put every listed object into one container (fetch each in turn).
---

# Collect objects into a container (`collect`)

`collect(objects: object_list, container: container_ref)`

Put every listed object into one container (fetch each in turn).

## When to use

Several objects must go into one container.

## Not to be confused with

- `fetch`: collect repeats fetch into one container.

## Inputs

- `objects` (`object_list`): Objects to gather.
- `container` (`container_ref`): The container.

## Call

Send one JSON object:

```json
{"contract": "collect", "args": {"objects": "<object_list>", "container": "<container>"}}
```

Argument formats:

- `container_ref`: an object annotated as an open container
- `object_list`: a non-empty list of object refs

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires hand_empty(hand=right); uncovered(container=$container).

## Preconditions (checked before moving)

- `hand_empty(hand=right)` — The given gripper holds nothing.
- `uncovered(container=$container)` — No lid rests on the container rim.

## Postconditions (checked after the action)

- `all_inside(objects=$objects, container=$container)` — Every listed object is inside the container.

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

