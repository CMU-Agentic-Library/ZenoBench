---
name: flip-object
description: Turn a flat object upside down where it lies: slide it to an edge, pinch the overhang, lift, roll the hand 180 deg, lay it back and release.
---

# Flip a flat object over (`flip`)

`flip(object: object_ref)`

Turn a flat object upside down where it lies: slide it to an edge, pinch the overhang, lift, roll the hand 180 deg, lay it back and release.

## When to use

A flat object must be turned upside down.

## Not to be confused with

- `rotate`: rotate turns about the vertical axis; flip turns the object upside down.

## Inputs

- `object` (`object_ref`): A flat object (book, plate, notebook) on a support.

## Call

Send one JSON object:

```json
{"contract": "flip", "args": {"object": "<object>"}}
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

Requires hand_empty(hand=right); base_near(place=$object).

## Preconditions (checked before moving)

- `hand_empty(hand=right)` — The given gripper holds nothing.
- `base_near(place=$object)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).

## Postconditions (checked after the action)

- `flipped(object=$object)` — Object's local z axis now points opposite to its direction at the start (dot <= -0.7).
- `hand_empty(hand=right)` — The given gripper holds nothing.

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

