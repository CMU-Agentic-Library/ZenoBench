---
name: regrasp-object
description: Set the held object down on a support and grasp it again with a fresh, centred grasp (recovery when the object has pivoted in the pinch).
---

# Regrasp a held object (`regrasp`)

`regrasp(object: object_ref, support: support_ref)`

Set the held object down on a support and grasp it again with a fresh, centred grasp (recovery when the object has pivoted in the pinch).

## When to use

The current grasp is unsuitable (wrong end, slipping) and the object can be set down.

## Not to be confused with

- `pick`: pick starts from an empty hand.
- `rotate`: rotate keeps the grasp; regrasp sets the object down and grasps again.

## Inputs

- `object` (`object_ref`): The held object.
- `support` (`support_ref`): Where to set it down briefly.

## Outputs

- `grasp` (`hand`): Grasp kind after the regrasp.

## Call

Send one JSON object:

```json
{"contract": "regrasp", "args": {"object": "<object>", "support": "<support>"}}
```

Argument formats:

- `object_ref`: a movable annotated scene object
- `support_ref`: an annotated horizontal support surface

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires holding(hand=right, object=$object); base_near(place=$support).

## Preconditions (checked before moving)

- `holding(hand=right, object=$object)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.
- `base_near(place=$support)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).

## Postconditions (checked after the action)

- `holding(hand=right, object=$object)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

