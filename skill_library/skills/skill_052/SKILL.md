---
name: arrange-objects
description: Place the listed objects on one support so that they are pairwise within a distance (a place setting).
---

# Arrange objects together (`arrange`)

`arrange(objects: object_list, support: support_ref, max_dist_m: positive_number)`

Place the listed objects on one support so that they are pairwise within a distance (a place setting).

## When to use

Several objects must be grouped together on one support (a setting).

## Not to be confused with

- `sweep`: arrange picks and places; sweep pushes.

## Inputs

- `objects` (`object_list`): Objects to group.
- `support` (`support_ref`): The surface.
- `max_dist_m` (`positive_number`, default 0.5): Pairwise distance limit.

## Call

Send one JSON object:

```json
{"contract": "arrange", "args": {"objects": "<object_list>", "support": "<support>", "max_dist_m": "<positive_number>"}}
```

Argument formats:

- `object_list`: a non-empty list of object refs
- `positive_number`: a number > 0
- `support_ref`: an annotated horizontal support surface

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

- `grouped(objects=$objects, support=$support, max_dist_m=$max_dist_m)` — Every listed object is on the support and pairwise within the distance.

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

