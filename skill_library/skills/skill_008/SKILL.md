---
name: straighten-waist
description: Return the waist pitch to upright.
---

# Straighten the waist (`straighten`)

`straighten()`

Return the waist pitch to upright.

## When to use

After a bend, before driving or carrying.

## Not to be confused with

- `stand`: stand raises the torso; straighten undoes a waist bend.

## Inputs

- none

## Call

Send one JSON object:

```json
{"contract": "straighten", "args": {}}
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

- `waist_straight()` — Waist pitch within 0.05 rad of upright.

## May invalidate

`waist_bent(*)`, `reachable(*)`, `in_view(*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

