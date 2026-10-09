---
name: heat-food
description: Bring food to a target temperature with an appliance and switch the heat off: in the closed microwave (start key + wait) or in a pot on the stove burner (power key on, wait, power key off).
---

# Heat food (`heat`)

`heat(food: object_ref, appliance: appliance_ref, temp_c: number)`

Bring food to a target temperature with an appliance and switch the heat off: in the closed microwave (start key + wait) or in a pot on the stove burner (power key on, wait, power key off).

## When to use

Food must reach a target temperature with the microwave or the stove.

## Not to be confused with

- `chill`: opposite direction, in the refrigerator.
- `press`: press does not wait.

## Inputs

- `food` (`object_ref`): The food item (has task-level thermal state).
- `appliance` (`appliance_ref`): kitchen_microwave or kitchen_stove.
- `temp_c` (`number`, default 60.0): Target temperature in degC.

## Outputs

- `temp_c` (`number`): Measured final temperature.

## Call

Send one JSON object:

```json
{"contract": "heat", "args": {"food": "<object>", "appliance": "<appliance>", "temp_c": "<number>"}}
```

Argument formats:

- `appliance_ref`: an articulated appliance with a thermal role (microwave, refrigerator)
- `number`: a finite number
- `object_ref`: a movable annotated scene object

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires hand_empty(hand=right); base_near(place=$appliance). Some bound nouns add preconditions (see Conditions that depend on the bound nouns).

## Preconditions (checked before moving)

- `hand_empty(hand=right)` — The given gripper holds nothing.
- `base_near(place=$appliance)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).

## Postconditions (checked after the action)

- `temperature_at_least(object=$food, temp_c=$temp_c)` — Task-level food temperature at or above the threshold.
- `not heating(appliance=$appliance)` — The appliance's heat source is on (microwave cycle or stove burner).

## Conditions that depend on the bound nouns

- when appliance.category == 'microwave': needs `in_appliance(object=$food, appliance=$appliance)`; needs `is_closed(articulated=$appliance)`
- when appliance.category == 'stove': needs `in_cookware_on_burner(food=$food, appliance=$appliance)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

