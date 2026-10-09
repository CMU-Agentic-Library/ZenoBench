---
name: navigate-place
description: Drive the holonomic base to a free stand-off pose next to a room, piece of furniture, support, articulated part or object. The arm is tucked when empty, or held in the compact carry pose with the load.
---

# Navigate to a place (`navigate`)

`navigate(destination: place_ref)`

Drive the holonomic base to a free stand-off pose next to a room, piece of furniture, support, articulated part or object. The arm is tucked when empty, or held in the compact carry pose with the load.

## When to use

The robot must be in another room or next to another piece of furniture.

## Not to be confused with

- `approach`: approach fine-parks so the arm reaches one target; navigate only gets near.
- `retreat`: retreat moves straight back from a place without a destination.

## Inputs

- `destination` (`place_ref`): Where to go: a room, furniture, support, articulated part or object.

## Outputs

- `base_pose` (`pose2d`): Measured base pose [x, y, yaw_deg] at arrival.

## Call

Send one JSON object:

```json
{"contract": "navigate", "args": {"destination": "<place>"}}
```

Argument formats:

- `place_ref`: a room, furniture, support, articulated part or object used as a destination

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

- `base_near(place=$destination)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).

## May invalidate

`base_near(*)`, `reachable(*)`, `facing(*)`, `in_view(*)`, `base_clear_of(*)`, `pointing_at(*)`, `presenting(*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

- no free stand-off pose
- no base path
- carried object slipped (Dropped)
