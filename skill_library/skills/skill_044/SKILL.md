---
name: chill-food
description: Keep food in the closed refrigerator until it is at or below a target temperature.
---

# Chill food (`chill`)

`chill(food: object_ref, appliance: appliance_ref, temp_c: number)`

Keep food in the closed refrigerator until it is at or below a target temperature.

## When to use

Food or a drink must cool in the refrigerator.

## Not to be confused with

- `heat`: opposite direction, with the microwave or stove.

## Inputs

- `food` (`object_ref`): The food item with thermal state.
- `appliance` (`appliance_ref`, default 'breakfast_fridge'): The refrigerator.
- `temp_c` (`number`, default 8.0): Maximum temperature in degC.

## Outputs

- `temp_c` (`number`): Measured final temperature.

## Call

Send one JSON object:

```json
{"contract": "chill", "args": {"food": "<object>", "appliance": "<appliance>", "temp_c": "<number>"}}
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

Requires in_appliance(object=$food, appliance=$appliance); is_closed(articulated=$appliance).

## Preconditions (checked before moving)

- `in_appliance(object=$food, appliance=$appliance)` — Object centre inside the appliance cavity box (microwave) or body box (refrigerator).
- `is_closed(articulated=$appliance)` — Joint within 0.10 rad (doors) or 4 cm (drawers) of closed.

## Postconditions (checked after the action)

- `temperature_at_most(object=$food, temp_c=$temp_c)` — Task-level food temperature at or below the threshold.

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

