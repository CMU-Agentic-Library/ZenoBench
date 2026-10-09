---
name: stir-container
description: Dip a held spoon's far end into a container and move it in a circle below the rim; succeeds after one full turn inside.
---

# Stir a container (`stir`)

`stir(container: container_ref, tool: tool_ref)`

Dip a held spoon's far end into a container and move it in a circle below the rim; succeeds after one full turn inside.

## When to use

The contents of a container must be stirred with a held utensil.

## Not to be confused with

- `dip`: dip goes in and out without circling.

## Inputs

- `container` (`container_ref`): The pot or bowl to stir.
- `tool` (`tool_ref`): The held utensil (spoon).

## Outputs

- `turns` (`number`): Measured turns of the tip inside the container.

## Call

Send one JSON object:

```json
{"contract": "stir", "args": {"container": "<container>", "tool": "<tool>"}}
```

Argument formats:

- `container_ref`: an object annotated as an open container
- `tool_ref`: an object tagged as a hand tool (sponge, spoon)

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires holding(hand=right, object=$tool); base_near(place=$container); uncovered(container=$container).

## Preconditions (checked before moving)

- `holding(hand=right, object=$tool)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.
- `base_near(place=$container)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).
- `uncovered(container=$container)` — No lid rests on the container rim.

## Postconditions (checked after the action)

- `stirred(container=$container)` — A held utensil tip completed one full circle inside the container below its rim.
- `holding(hand=right, object=$tool)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

