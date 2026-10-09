---
name: hide-object
description: Make an object invisible from outside: put it into a container and cover that container with its lid, or put it on a shelf inside a cabinet and close the cabinet.
---

# Hide an object (`hide`)

`hide(object: object_ref, receptacle: receptacle_ref, lid: lid_ref?)`

Make an object invisible from outside: put it into a container and cover that container with its lid, or put it on a shelf inside a cabinet and close the cabinet.

## When to use

An object must end up out of sight inside a closed container.

## Not to be confused with

- `collect`: hide also covers the container.

## Inputs

- `object` (`object_ref`): The object to hide.
- `receptacle` (`receptacle_ref`): A lidded container or a cabinet interior shelf.
- `lid` (`lid_ref`, optional): The lid to use for a container.

## Call

Send one JSON object:

```json
{"contract": "hide", "args": {"object": "<object>", "receptacle": "<receptacle>"}}
```

Argument formats:

- `lid_ref`: an object tagged as a lid
- `object_ref`: a movable annotated scene object
- `receptacle_ref`: a support surface or an open container

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires hand_empty(hand=right). Some bound nouns add preconditions (see Conditions that depend on the bound nouns).

## Preconditions (checked before moving)

- `hand_empty(hand=right)` — The given gripper holds nothing.

## Postconditions (checked after the action)

- `hidden(object=$object)` — Object is inside a lid-covered container or on a shelf inside a closed cabinet.
- `hand_empty(hand=right)` — The given gripper holds nothing.

## Conditions that depend on the bound nouns

- when receptacle.kind == 'object' and args.lid: needs `uncovered(container=$receptacle)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

