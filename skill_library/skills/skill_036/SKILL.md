---
name: upright-object
description: Make a lying object stand: pinch it, rotate its local up axis to vertical in the hand, and set it down upright on the same support.
---

# Stand an object upright (`upright`)

`upright(object: object_ref)`

Make a lying object stand: pinch it, rotate its local up axis to vertical in the hand, and set it down upright on the same support.

## When to use

A lying object must stand on its base again.

## Not to be confused with

- `tip`: opposite direction.

## Inputs

- `object` (`object_ref`): A lying object.

## Call

Send one JSON object:

```json
{"contract": "upright", "args": {"object": "<object>"}}
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

Requires hand_empty(hand=right); base_near(place=$object); lying(object=$object).

## Preconditions (checked before moving)

- `hand_empty(hand=right)` — The given gripper holds nothing.
- `base_near(place=$object)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).
- `lying(object=$object)` — Object on its side: longest axis within 60 deg of horizontal and vertical extent <= 60 % of its length.

## Postconditions (checked after the action)

- `upright(object=$object)` — Object z axis within 20 deg of vertical.
- `hand_empty(hand=right)` — The given gripper holds nothing.

## Conditions that depend on the bound nouns

- when 'top_pinch' in object.grasp_types: ensures `on(object=$object, support=@object.support)`

## May invalidate

`lying($object)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

