---
name: stop-appliance
description: Switch an appliance's heat off: press the stove power key off, or open the microwave door, which ends its cycle.
---

# Stop an appliance (`stop`)

`stop(appliance: appliance_ref)`

Switch an appliance's heat off: press the stove power key off, or open the microwave door, which ends its cycle.

## When to use

An appliance that is heating must be switched off.

## Not to be confused with

- `press`: press does not guarantee the heat is off.
- `close`: close does not stop a stove.

## Inputs

- `appliance` (`appliance_ref`): kitchen_stove or kitchen_microwave.

## Call

Send one JSON object:

```json
{"contract": "stop", "args": {"appliance": "<appliance>"}}
```

Argument formats:

- `appliance_ref`: an articulated appliance with a thermal role (microwave, refrigerator)

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires hand_empty(hand=right); base_near(place=$appliance).

## Preconditions (checked before moving)

- `hand_empty(hand=right)` — The given gripper holds nothing.
- `base_near(place=$appliance)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).

## Postconditions (checked after the action)

- `not heating(appliance=$appliance)` — The appliance's heat source is on (microwave cycle or stove burner).

## Conditions that depend on the bound nouns

- when appliance.category == 'microwave': ensures `is_open(articulated=$appliance)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

