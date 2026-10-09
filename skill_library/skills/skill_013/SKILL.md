---
name: search-object
description: Find an object whose location is unknown: visit the supports of a room in order of distance and aim the head at each surface until the object is seen.
---

# Search for an object (`search`)

`search(object: object_ref, region: room_ref?)`

Find an object whose location is unknown: visit the supports of a room in order of distance and aim the head at each surface until the object is seen.

## When to use

The location of an object is unknown in the current room.

## Not to be confused with

- `explore`: explore covers a room without a target.

## Inputs

- `object` (`object_ref`): The object to find.
- `region` (`room_ref`, optional): Room to search; default the robot's room.

## Outputs

- `found_on` (`support_ref`): Support under the object when it was seen.
- `visited` (`object_list`): Furniture visited in order.

## Call

Send one JSON object:

```json
{"contract": "search", "args": {"object": "<object>"}}
```

Argument formats:

- `object_ref`: a movable annotated scene object
- `room_ref`: an annotated room

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

- `observed(target=$object)` — The robot saw the target in its head camera during this episode (set by look, search, inspect, explore).

## May invalidate

`base_near(*)`, `reachable(*)`, `facing(*)`, `in_view(*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

