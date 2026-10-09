---
name: empty-container
description: Take every object out of a container and put it on/into a destination receptacle.
---

# Empty a container (`empty`)

`empty(container: container_ref, receptacle: receptacle_ref)`

Take every object out of a container and put it on/into a destination receptacle.

## When to use

A container must be emptied into another container or onto a surface.

## Not to be confused with

- `pour`: empty may also pick items out one by one.

## Inputs

- `container` (`container_ref`): The container to empty.
- `receptacle` (`receptacle_ref`): Where the contents go (a container if they are poured).

## Outputs

- `moved` (`object_list`): Objects that were taken out.

## Call

Send one JSON object:

```json
{"contract": "empty", "args": {"container": "<container>", "receptacle": "<receptacle>"}}
```

Argument formats:

- `container_ref`: an object annotated as an open container
- `receptacle_ref`: a support surface or an open container

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

- `container_empty(container=$container)` — No annotated object is inside the container.

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

