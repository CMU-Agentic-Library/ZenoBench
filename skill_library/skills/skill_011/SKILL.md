---
name: look-target
description: Aim the head camera at a target (turning the base if it is outside the head yaw range) and record every annotated object in view as observed.
---

# Look at a target (`look`)

`look(target: entity_ref)`

Aim the head camera at a target (turning the base if it is outside the head yaw range) and record every annotated object in view as observed.

## When to use

A known target must be brought into the head camera view.

## Not to be confused with

- `inspect`: inspect reports a receptacle's contents; look only aims the camera.
- `search`: search visits several places to find an unseen object.

## Inputs

- `target` (`entity_ref`): What to look at.

## Outputs

- `seen` (`object_list`): Objects in the head camera frustum with clear line of sight.

## Call

Send one JSON object:

```json
{"contract": "look", "args": {"target": "<entity>"}}
```

Argument formats:

- `entity_ref`: any annotated object, support, articulated part or button

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

- `in_view(target=$target)` — Target point inside the head camera frustum, within 5 m, line of sight not blocked by furniture boxes.
- `observed(target=$target)` — The robot saw the target in its head camera during this episode (set by look, search, inspect, explore).

## May invalidate

`in_view(*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

