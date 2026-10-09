---
name: wait-duration
description: Do nothing for the given simulated time (an appliance cycle running, an object settling).
---

# Wait for a duration (`wait`)

`wait(seconds: positive_number)`

Do nothing for the given simulated time (an appliance cycle running, an object settling).

## When to use

Something must happen over time (cooling, settling) and the robot should not act.

## Not to be confused with

- `heat`: heat waits for a measured temperature; wait for a fixed time.

## Inputs

- `seconds` (`positive_number`, default 5.0): How long to wait.

## Call

Send one JSON object:

```json
{"contract": "wait", "args": {"seconds": "<positive_number>"}}
```

Argument formats:

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

- `waited(seconds=$seconds)` — At least the given simulated time passed during the Contract.

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

