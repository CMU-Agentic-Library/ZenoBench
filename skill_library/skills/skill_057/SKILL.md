---
name: identify-object
description: Look at an object and report its category and tags (asset annotation) once it is in the head camera view.
---

# Identify an object (`identify`)

`identify(object: object_ref)`

Look at an object and report its category and tags (asset annotation) once it is in the head camera view.

## When to use

The category or identity of a visible object must be confirmed.

## Not to be confused with

- `look`: look only aims the camera.
- `measure`: measure reports dimensions.

## Inputs

- `object` (`object_ref`): The object to identify.

## Outputs

- `category` (`tag`): Asset category.
- `tags` (`object_list`): Annotated tags.

## Call

Send one JSON object:

```json
{"contract": "identify", "args": {"object": "<object>"}}
```

Argument formats:

- `object_ref`: a movable annotated scene object

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

- `identified(object=$object)` — The robot recorded the object's category while it was in the head camera view.
- `in_view(target=$object)` — Target point inside the head camera frustum, within 5 m, line of sight not blocked by furniture boxes.

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

