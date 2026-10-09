---
name: bend-waist
description: Pitch the waist forward to extend the reach over a deep surface.
---

# Bend the waist (`bend`)

`bend(pitch_rad: positive_number?)`

Pitch the waist forward to extend the reach over a deep surface.

## When to use

A target is just beyond arm reach over a counter and leaning forward helps.

## Not to be confused with

- `crouch`: crouch lowers the torso; bend tilts the waist.

## Inputs

- `pitch_rad` (`positive_number`, optional): Forward pitch in rad (max 0.69); omit for the maximum.

## Call

Send one JSON object:

```json
{"contract": "bend", "args": {}}
```

Argument formats:

- `positive_number`: a number > 0

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

- `waist_bent(min_pitch_rad=0.2)` — Waist pitched forward by at least the given angle.

## May invalidate

`waist_straight()`, `reachable(*)`, `in_view(*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

