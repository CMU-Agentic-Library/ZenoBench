---
name: drop-object
description: Hold the object 5 cm above a container's opening, centred, and let go; the object falls in.
---

# Drop an object into a container (`drop`)

`drop(object: object_ref, container: container_ref)`

Hold the object 5 cm above a container's opening, centred, and let go; the object falls in.

## When to use

A held object must go into an open container from above without a precise pose.

## Not to be confused with

- `place`: place lowers the object onto the container floor before opening.

## Inputs

- `object` (`object_ref`): The held object.
- `container` (`container_ref`): The open container.

## Call

Send one JSON object:

```json
{"contract": "drop", "args": {"object": "<object>", "container": "<container>"}}
```

Argument formats:

- `container_ref`: an object annotated as an open container
- `object_ref`: a movable annotated scene object

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires holding(hand=right, object=$object); base_near(place=$container); uncovered(container=$container).

## Preconditions (checked before moving)

- `holding(hand=right, object=$object)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.
- `base_near(place=$container)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).
- `uncovered(container=$container)` — No lid rests on the container rim.

## Postconditions (checked after the action)

- `inside(object=$object, container=$container)` — Object centre inside the container's wall profile, between its floor and 3 cm above the rim.
- `hand_empty(hand=right)` — The given gripper holds nothing.

## May invalidate

`holding(right,$object)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

