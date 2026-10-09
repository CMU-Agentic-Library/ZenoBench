---
name: press-button
description: Press an annotated appliance button with the closed fingertips and retract: the microwave door key, the microwave start key, or the stove power key (which toggles the burner).
---

# Press a button (`press`)

`press(button: button_ref)`

Press an annotated appliance button with the closed fingertips and retract: the microwave door key, the microwave start key, or the stove power key (which toggles the burner).

## When to use

A button (microwave keys, stove power key) must be pressed.

## Not to be confused with

- `heat`: heat guarantees a temperature; press guarantees only the key press.
- `open`: open guarantees the door is open.

## Inputs

- `button` (`button_ref`): E.g. kitchen_microwave/door_button, kitchen_stove/power_button.

## Call

Send one JSON object:

```json
{"contract": "press", "args": {"button": "<button>"}}
```

Argument formats:

- `button_ref`: an annotated appliance button, written <appliance>/<button>

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires hand_empty(hand=right); base_near(place=@button.appliance). Some bound nouns add preconditions (see Conditions that depend on the bound nouns).

## Preconditions (checked before moving)

- `hand_empty(hand=right)` — The given gripper holds nothing.
- `base_near(place=@button.appliance)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).

## Postconditions (checked after the action)

- `button_pressed(button=$button)` — A measured press of this button happened during the Contract.
- `hand_empty(hand=right)` — The given gripper holds nothing.

## Conditions that depend on the bound nouns

- when button.button == 'start_button': needs `is_closed(articulated=@button.appliance)`; ensures `heating(appliance=@button.appliance)`

## May invalidate

`arm_stowed(right)`, `reachable(*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

