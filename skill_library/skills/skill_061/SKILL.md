---
name: nod-head
description: Pitch the head down and up twice (acknowledgement gesture).
---

# Nod the head (`nod`)

`nod()`

Pitch the head down and up twice (acknowledgement gesture).

## When to use

Acknowledging an instruction.

## Not to be confused with

- `wave`: wave uses the arm; nod uses the head.

## Inputs

- none

## Call

Send one JSON object:

```json
{"contract": "nod", "args": {}}
```

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

No precondition.

## Preconditions (checked before moving)

- none

## Postconditions (checked after the action)

- `nodded()` — The head performed a measured nod (>= 2 pitch cycles of >= 0.2 rad).

## May invalidate

`in_view(*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

