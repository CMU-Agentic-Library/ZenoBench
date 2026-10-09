---
name: stand-torso
description: Raise the torso lift to its top travel height.
---

# Stand up to full height (`stand`)

`stand()`

Raise the torso lift to its top travel height.

## When to use

After a crouch, before driving or reaching high.

## Not to be confused with

- `lift`: lift raises a held object, stand raises the body.
- `straighten`: straighten undoes a waist bend; stand raises the torso.

## Inputs

- none

## Call

Send one JSON object:

```json
{"contract": "stand", "args": {}}
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

- `torso_raised()` — Torso lift within 3 cm of its highest position (travel height).

## May invalidate

`torso_lowered()`, `reachable(*)`, `in_view(*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

