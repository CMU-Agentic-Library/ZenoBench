---
name: pour-contents
description: Hold the cup's far lip over a container, turn the cup about that lip up to 90 deg and return it upright; succeeds when at least half of the loose items that were in the cup are inside the target. A rim-held cup tilts away from the pinch; a handle-held cup rolls sideways about the forearm.
---

# Pour contents into a container (`pour`)

`pour(source: container_ref, target: container_ref)`

Hold the cup's far lip over a container, turn the cup about that lip up to 90 deg and return it upright; succeeds when at least half of the loose items that were in the cup are inside the target. A rim-held cup tilts away from the pinch; a handle-held cup rolls sideways about the forearm.

## When to use

Loose contents of a held container must go into another container.

## Not to be confused with

- `drop`: drop releases the held object itself; pour tips out its contents.

## Inputs

- `source` (`container_ref`): The held cup or mug with loose items.
- `target` (`container_ref`): The receiving container.

## Outputs

- `moved` (`object_list`): Items now inside the target.

## Call

Send one JSON object:

```json
{"contract": "pour", "args": {"source": "<container>", "target": "<container>"}}
```

Argument formats:

- `container_ref`: an object annotated as an open container

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires holding(hand=right, object=$source); base_near(place=$target); uncovered(container=$target); not container_empty(container=$source).

## Preconditions (checked before moving)

- `holding(hand=right, object=$source)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.
- `base_near(place=$target)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).
- `uncovered(container=$target)` — No lid rests on the container rim.
- `not container_empty(container=$source)` — No annotated object is inside the container.

## Postconditions (checked after the action)

- `poured_into(source=$source, target=$target)` — At least half of the items that were inside the source are now inside the target.
- `holding(hand=right, object=$source)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

