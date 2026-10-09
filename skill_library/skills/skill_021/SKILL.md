---
name: release-object
description: Open one gripper where the object already rests (e.g. let go of a braced pot, or of an object that was set down by another action) and back the fingers off.
---

# Release an object (`release`)

`release(object: object_ref, hand: hand)`

Open one gripper where the object already rests (e.g. let go of a braced pot, or of an object that was set down by another action) and back the fingers off.

## When to use

The hand must open in place (the object is already supported).

## Not to be confused with

- `drop`: drop moves above a container first; release does not move the object.
- `place`: place moves to a pose first; release only opens the hand.

## Inputs

- `object` (`object_ref`): The object in the hand.
- `hand` (`hand`, one of 'right', 'left', default 'right'): Which gripper opens.

## Call

Send one JSON object:

```json
{"contract": "release", "args": {"object": "<object>", "hand": "<hand>"}}
```

Argument formats:

- `hand`: "right" or "left"
- `object_ref`: a movable annotated scene object

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires holding(hand=$hand, object=$object).

## Preconditions (checked before moving)

- `holding(hand=$hand, object=$object)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.

## Postconditions (checked after the action)

- `hand_empty(hand=$hand)` — The given gripper holds nothing.

## May invalidate

`holding($hand,$object)`, `steadied($object)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

