---
name: restore-object
description: Return an object to the support it occupied at the start of the episode.
---

# Restore an object to its place (`restore`)

`restore(object: object_ref)`

Return an object to the support it occupied at the start of the episode.

## When to use

An object must return to where it was at the start.

## Not to be confused with

- `fetch`: restore's destination is the object's initial support.

## Inputs

- `object` (`object_ref`): The displaced object.

## Call

Send one JSON object:

```json
{"contract": "restore", "args": {"object": "<object>"}}
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

Requires hand_empty(hand=right).

## Preconditions (checked before moving)

- `hand_empty(hand=right)` — The given gripper holds nothing.

## Postconditions (checked after the action)

- `at_initial_place(object=$object)` — Object is back on the support it occupied when the episode started.
- `hand_empty(hand=right)` — The given gripper holds nothing.

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

