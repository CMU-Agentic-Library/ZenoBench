---
name: explore-room
description: Cover a room from up to three viewpoints with a left/centre/right head sweep; succeeds when at least 75 % of the room's supports and objects were seen.
---

# Explore a room (`explore`)

`explore(room: room_ref)`

Cover a room from up to three viewpoints with a left/centre/right head sweep; succeeds when at least 75 % of the room's supports and objects were seen.

## When to use

A room must be surveyed before planning (unknown layout or objects).

## Not to be confused with

- `search`: search looks for one object and stops when found.

## Inputs

- `room` (`room_ref`): The room to cover.

## Outputs

- `seen` (`object_list`): Objects observed during the sweep.

## Call

Send one JSON object:

```json
{"contract": "explore", "args": {"room": "<room>"}}
```

Argument formats:

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

- `room_explored(room=$room)` — At least 75 % of the room's head-camera viewpoints were covered.

## May invalidate

`base_near(*)`, `reachable(*)`, `facing(*)`, `in_view(*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

