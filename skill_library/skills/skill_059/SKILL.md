---
name: count-category
description: Sweep the head from the current place and count the visible objects whose asset or tag matches.
---

# Count objects of a category (`count`)

`count(category: tag)`

Sweep the head from the current place and count the visible objects whose asset or tag matches.

## When to use

The number of objects of one category in view must be known.

## Not to be confused with

- `identify`: count returns a number for one category.

## Inputs

- `category` (`tag`): Asset name or tag, e.g. "cherry_tomato", "fruit".

## Outputs

- `count` (`number`): Number of visible matches.
- `objects` (`object_list`): The matches.

## Call

Send one JSON object:

```json
{"contract": "count", "args": {"category": "<tag>"}}
```

Argument formats:

- `tag`: an asset tag or asset name, e.g. "fruit", "toy", "cherry_tomato"

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

- `counted(category=$category)` — The robot recorded how many objects of the category it sees from its current place.

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

