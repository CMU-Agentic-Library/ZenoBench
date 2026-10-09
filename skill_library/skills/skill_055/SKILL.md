---
name: sidestep-base
description: Move the base sideways by a signed distance (left positive) without turning, also while carrying a load; aligns the arm with a target that is a little to the side.
---

# Sidestep the base (`sidestep`)

`sidestep(distance_m: number)`

Move the base sideways by a signed distance (left positive) without turning, also while carrying a load; aligns the arm with a target that is a little to the side.

## When to use

The robot must shift sideways a few centimetres without turning (align with a target).

## Not to be confused with

- `retreat`: retreat moves straight back; sidestep moves sideways.
- `face`: face turns in place; sidestep keeps the heading.

## Inputs

- `distance_m` (`number`): Lateral displacement in metres (left > 0).

## Call

Send one JSON object:

```json
{"contract": "sidestep", "args": {"distance_m": "<number>"}}
```

Argument formats:

- `number`: a finite number

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

- `sidestepped(distance_m=$distance_m)` — Base moved sideways by the signed distance (left > 0) within 3 cm, heading unchanged within 3 deg.

## May invalidate

`base_near(*)`, `reachable(*)`, `facing(*)`, `in_view(*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

