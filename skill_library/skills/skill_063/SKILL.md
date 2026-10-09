---
name: hover-object
description: Hold the carried object centred 6 cm above a target (a container opening, a spot on a surface) without releasing it, e.g. to show or to align before a drop.
---

# Hover a held object over a target (`hover`)

`hover(object: object_ref, target: entity_ref)`

Hold the carried object centred 6 cm above a target (a container opening, a spot on a surface) without releasing it, e.g. to show or to align before a drop.

## When to use

A held object must be positioned over a target before dropping or pouring.

## Not to be confused with

- `drop`: hover keeps the grasp.
- `lift`: lift has no target point.

## Inputs

- `object` (`object_ref`): The right-held object.
- `target` (`entity_ref`): What to hover over.

## Call

Send one JSON object:

```json
{"contract": "hover", "args": {"object": "<object>", "target": "<entity>"}}
```

Argument formats:

- `entity_ref`: any annotated object, support, articulated part or button
- `object_ref`: a movable annotated scene object

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires holding(hand=right, object=$object); base_near(place=$target).

## Preconditions (checked before moving)

- `holding(hand=right, object=$object)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.
- `base_near(place=$target)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).

## Postconditions (checked after the action)

- `hovering_over(object=$object, target=$target)` — The right-held object's bottom is 3-15 cm above the target's top, centred within 4 cm.
- `holding(hand=right, object=$object)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

