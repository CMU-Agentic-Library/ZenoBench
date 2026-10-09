---
name: crouch-torso
description: Lower the torso lift to its bottom (or a requested height) for floor and low-shelf work.
---

# Crouch the torso (`crouch`)

`crouch(height_m: number?)`

Lower the torso lift to its bottom (or a requested height) for floor and low-shelf work.

## When to use

The next target is low (floor, low shelf) or the head must look under something.

## Not to be confused with

- `bend`: bend pitches the waist forward; crouch lowers the torso vertically.

## Inputs

- `height_m` (`number`, optional): Optional torso joint target in [-0.54, 0]; omit for the lowest.

## Call

Send one JSON object:

```json
{"contract": "crouch", "args": {}}
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

- `not torso_raised()` — Torso lift within 3 cm of its highest position (travel height).

## Conditions that depend on the bound nouns

- when args.height_m: ensures `torso_at(height_m=$height_m)`
- when always: ensures `torso_lowered()`

## May invalidate

`torso_raised()`, `torso_lowered()`, `torso_at(*)`, `reachable(*)`, `in_view(*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

