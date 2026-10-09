---
name: approach-target
description: Park the base where the right arm has a collision-free IK solution at the target's reach pose: 10 cm above an object or support, the handle pre-grasp of a door or drawer, 8 cm in front of a button.
---

# Approach a manipulation target (`approach`)

`approach(target: entity_ref, pass_by: pose2d?)`

Park the base where the right arm has a collision-free IK solution at the target's reach pose: 10 cm above an object or support, the handle pre-grasp of a door or drawer, 8 cm in front of a button.

## When to use

Right before a contact action on one specific target.

## Not to be confused with

- `navigate`: navigate goes to a region; approach verifies arm IK for one target.

## Inputs

- `target` (`entity_ref`): The object, support, handle-bearing part or button to reach.
- `pass_by` (`pose2d`, optional): Optional base waypoint: reach toward the target while driving past it.

## Outputs

- `base_pose` (`pose2d`): Base pose at which reachability was verified.

## Call

Send one JSON object:

```json
{"contract": "approach", "args": {"target": "<entity>"}}
```

Argument formats:

- `entity_ref`: any annotated object, support, articulated part or button
- `pose2d`: a base pose [x, y, yaw_deg] in metres and degrees

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires base_near(place=$target).

## Preconditions (checked before moving)

- `base_near(place=$target)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).

## Postconditions (checked after the action)

- `reachable(target=$target)` — From the current base pose the right TCP has a collision-free IK solution 10 cm above the target (handle pre-grasp for doors, 8 cm in front of a button).

## May invalidate

`reachable(*)`, `facing(*)`, `in_view(*)`, `pointing_at(*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

- no base pose reaches the target
- IK fails after parking
