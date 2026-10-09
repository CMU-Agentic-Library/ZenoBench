---
name: retreat-obstacle
description: Back the base straight away from a piece of furniture, appliance or object until it is at least the given distance away; a held load stays held.
---

# Retreat from an obstacle (`retreat`)

`retreat(obstacle: place_ref, distance_m: positive_number)`

Back the base straight away from a piece of furniture, appliance or object until it is at least the given distance away; a held load stays held.

## When to use

The base is too close to open a door, turn, or start a path.

## Not to be confused with

- `navigate`: retreat has no destination; it only increases clearance.

## Inputs

- `obstacle` (`place_ref`): What to back away from.
- `distance_m` (`positive_number`, default 0.4): Required clearance from the obstacle footprint.

## Outputs

- `moved_m` (`number`): Measured base displacement.

## Call

Send one JSON object:

```json
{"contract": "retreat", "args": {"obstacle": "<place>", "distance_m": "<positive_number>"}}
```

Argument formats:

- `place_ref`: a room, furniture, support, articulated part or object used as a destination
- `positive_number`: a number > 0

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

- `base_clear_of(place=$obstacle, distance_m=$distance_m)` — Base centre at least the given distance from the place's footprint.

## May invalidate

`base_near(*)`, `reachable(*)`, `facing(*)`, `in_view(*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

- the path behind the base is blocked
