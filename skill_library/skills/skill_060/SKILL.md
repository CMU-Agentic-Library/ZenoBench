---
name: wave-hand
description: Raise the empty right hand at head height and swing it (greeting / attention gesture).
---

# Wave the hand (`wave`)

`wave()`

Raise the empty right hand at head height and swing it (greeting / attention gesture).

## When to use

Greeting or getting attention.

## Not to be confused with

- `point`: point indicates a target; wave is a greeting.

## Inputs

- none

## Call

Send one JSON object:

```json
{"contract": "wave", "args": {}}
```

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

- `waved()` — The right hand performed a measured wave (>= 2 lateral swings at head height).
- `hand_empty(hand=right)` — The given gripper holds nothing.

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

