---
name: tip-object
description: Push a standing tall object near its top so it falls onto its side on the same support (lays down a carton or bottle that is too tall to top-pinch).
---

# Tip an object over (`tip`)

`tip(object: object_ref)`

Push a standing tall object near its top so it falls onto its side on the same support (lays down a carton or bottle that is too tall to top-pinch).

## When to use

An upright object must be laid on its side.

## Not to be confused with

- `upright`: upright makes a lying object stand.

## Inputs

- `object` (`object_ref`): A standing tall object.

## Call

Send one JSON object:

```json
{"contract": "tip", "args": {"object": "<object>"}}
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

Requires hand_empty(hand=right); base_near(place=$object); upright(object=$object).

## Preconditions (checked before moving)

- `hand_empty(hand=right)` — The given gripper holds nothing.
- `base_near(place=$object)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).
- `upright(object=$object)` — Object z axis within 20 deg of vertical.

## Postconditions (checked after the action)

- `lying(object=$object)` — Object on its side: longest axis within 60 deg of horizontal and vertical extent <= 60 % of its length.

## May invalidate

`upright($object)`, `at_initial_place($object)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

