---
name: handover-object
description: Transfer a right-held object into the left gripper and open the right gripper.
---

# Hand an object over to the left hand (`handover`)

`handover(object: object_ref)`

Transfer a right-held object into the left gripper and open the right gripper.

## When to use

The right hand must be freed while the object stays held (by the left hand).

## Not to be confused with

- `release`: release lets the object go; handover keeps it held by the left hand.

## Inputs

- `object` (`object_ref`): The right-held object.

## Call

Send one JSON object:

```json
{"contract": "handover", "args": {"object": "<object>"}}
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

Requires holding(hand=right, object=$object); hand_empty(hand=left).

## Preconditions (checked before moving)

- `holding(hand=right, object=$object)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.
- `hand_empty(hand=left)` — The given gripper holds nothing.

## Postconditions (checked after the action)

- `holding(hand=left, object=$object)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.
- `hand_empty(hand=right)` — The given gripper holds nothing.

## May invalidate

`holding(right,$object)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

