---
name: sort-objects
description: Put each listed object into the container mapped to its category tag (e.g. fruit -> basket, toy -> toy box).
---

# Sort objects by category (`sort`)

`sort(objects: object_list, rule: category_map)`

Put each listed object into the container mapped to its category tag (e.g. fruit -> basket, toy -> toy box).

## When to use

Objects must go to destinations by category.

## Not to be confused with

- `collect`: sort chooses a destination per category.

## Inputs

- `objects` (`object_list`): Objects to sort.
- `rule` (`category_map`): Tag -> destination mapping (a container or a support), e.g. {"fruit": "fruit_basket"}.

## Call

Send one JSON object:

```json
{"contract": "sort", "args": {"objects": "<object_list>", "rule": "<category_map>"}}
```

Argument formats:

- `category_map`: an object tag -> container ref mapping
- `object_list`: a non-empty list of object refs

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires hand_empty(hand=right).

## Preconditions (checked before moving)

- `hand_empty(hand=right)` — The given gripper holds nothing.

## Postconditions (checked after the action)

- `sorted_by_category(objects=$objects, rule=$rule)` — Each listed object is inside the container (or on the support) mapped to one of its tags.

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

