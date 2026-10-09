---
name: close-articulated
description: Close a door, drawer or appliance door to within 0.10 rad / 4 cm of closed. A powered microwave door closes from its hinge-clearance pose, also while the robot carries a load.
---

# Close a door or drawer (`close`)

`close(articulated: articulated_ref)`

Close a door, drawer or appliance door to within 0.10 rad / 4 cm of closed. A powered microwave door closes from its hinge-clearance pose, also while the robot carries a load.

## When to use

A door, drawer or appliance must be closed (before heating, after taking out).

## Not to be confused with

- `open`: opposite direction.

## Inputs

- `articulated` (`articulated_ref`): The open part.

## Outputs

- `joint` (`number`): Measured joint value.

## Call

Send one JSON object:

```json
{"contract": "close", "args": {"articulated": "<articulated>"}}
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

- `is_closed(articulated=$articulated)` — Joint within 0.10 rad (doors) or 4 cm (drawers) of closed.

## Conditions that depend on the bound nouns

- when articulated.has_handle: needs `hand_empty(hand=right)`
- when always: needs `hand_empty(hand=right)`

## May invalidate

`is_open($articulated)`, `base_near(*)`, `reachable(*)`, `facing(*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

