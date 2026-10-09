---
name: clear-support
description: Remove every object from a support surface to a destination receptacle.
---

# Clear a support (`clear`)

`clear(support: support_ref, receptacle: receptacle_ref)`

Remove every object from a support surface to a destination receptacle.

## When to use

Every object must be removed from one support.

## Not to be confused with

- `collect`: clear is defined by the source support, not by a list of objects.

## Inputs

- `support` (`support_ref`): The surface to clear.
- `receptacle` (`receptacle_ref`): Where the objects go.

## Outputs

- `moved` (`object_list`): Objects that were removed.

## Call

Send one JSON object:

```json
{"contract": "clear", "args": {"support": "<support>", "receptacle": "<receptacle>"}}
```

Argument formats:

- `receptacle_ref`: a support surface or an open container
- `support_ref`: an annotated horizontal support surface

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

- `support_clear(support=$support)` — No annotated object rests on the support.

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

