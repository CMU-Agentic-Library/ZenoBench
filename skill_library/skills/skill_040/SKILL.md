---
name: open-articulated
description: Open a door, drawer, refrigerator door or microwave door to its annotated open value. The method is chosen automatically from the part: powered microwave (door button + hinge), refrigerator handle, drawer handle pull, hinged door side-hook ride, or a door opened by the right hand while the left hand holds a load.
---

# Open a door or drawer (`open`)

`open(articulated: articulated_ref)`

Open a door, drawer, refrigerator door or microwave door to its annotated open value. The method is chosen automatically from the part: powered microwave (door button + hinge), refrigerator handle, drawer handle pull, hinged door side-hook ride, or a door opened by the right hand while the left hand holds a load.

## When to use

A door, drawer or appliance must be opened before reaching inside.

## Not to be confused with

- `press`: press only pushes a button; open guarantees the door is open.

## Inputs

- `articulated` (`articulated_ref`): The door, drawer or appliance door.

## Outputs

- `joint` (`number`): Measured joint value.

## Call

Send one JSON object:

```json
{"contract": "open", "args": {"articulated": "<articulated>"}}
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

Requires base_near(place=$articulated). Some bound nouns add preconditions (see Conditions that depend on the bound nouns).

## Preconditions (checked before moving)

- `base_near(place=$articulated)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).

## Postconditions (checked after the action)

- `is_open(articulated=$articulated)` — Joint at least 60 % of the way from closed to its annotated open value.

## Conditions that depend on the bound nouns

- when articulated.powered: needs `hand_empty(hand=right)`
- when robot.left_held and articulated.type == 'revolute': needs `hand_empty(hand=right)`
- when articulated.category == 'refrigerator': needs `hand_empty(hand=right)`
- when articulated.type == 'prismatic': needs `hand_empty(hand=right)`
- when articulated.type == 'revolute': needs `hand_empty(hand=right)`

## May invalidate

`is_closed($articulated)`, `base_near(*)`, `reachable(*)`, `facing(*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

