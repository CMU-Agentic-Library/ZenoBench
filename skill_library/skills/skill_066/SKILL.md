---
name: knock-articulated
description: Tap a closed door or drawer panel twice with the closed fingertips beside its handle; the panel must stay closed.
---

# Knock on a door (`knock`)

`knock(articulated: articulated_ref)`

Tap a closed door or drawer panel twice with the closed fingertips beside its handle; the panel must stay closed.

## When to use

A closed door must be knocked on (check, signal) without opening it.

## Not to be confused with

- `open`: knock must leave the door closed.

## Inputs

- `articulated` (`articulated_ref`): The closed door or drawer.

## Call

Send one JSON object:

```json
{"contract": "knock", "args": {"articulated": "<articulated>"}}
```

Argument formats:

- `articulated_ref`: an annotated door, drawer or appliance door

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires hand_empty(hand=right); base_near(place=$articulated); is_closed(articulated=$articulated).

## Preconditions (checked before moving)

- `hand_empty(hand=right)` — The given gripper holds nothing.
- `base_near(place=$articulated)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).
- `is_closed(articulated=$articulated)` — Joint within 0.10 rad (doors) or 4 cm (drawers) of closed.

## Postconditions (checked after the action)

- `knocked(articulated=$articulated)` — Two measured fingertip contacts on the closed panel during the Contract; the joint moved < 0.05.
- `is_closed(articulated=$articulated)` — Joint within 0.10 rad (doors) or 4 cm (drawers) of closed.

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

