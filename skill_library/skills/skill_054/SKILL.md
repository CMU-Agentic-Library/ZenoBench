---
name: swap-objects
description: Exchange the positions of two objects on their supports via a free buffer spot.
---

# Swap two objects (`swap`)

`swap(a: object_ref, b: object_ref)`

Exchange the positions of two objects on their supports via a free buffer spot.

## When to use

Two objects must exchange places.

## Not to be confused with

- `restore`: swap exchanges two objects.

## Inputs

- `a` (`object_ref`): First object.
- `b` (`object_ref`): Second object.

## Call

Send one JSON object:

```json
{"contract": "swap", "args": {"a": "<object>", "b": "<object>"}}
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

- `positions_swapped(a=$a, b=$b)` — Each object now rests within 6 cm of the other's starting position on its starting support.
- `hand_empty(hand=right)` — The given gripper holds nothing.

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

