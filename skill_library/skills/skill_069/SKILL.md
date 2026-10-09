---
name: dip-utensil
description: Lower a held spoon's far end into a container below its rim, hold it there and lift it out.
---

# Dip a utensil (`dip`)

`dip(tool: tool_ref, container: container_ref)`

Lower a held spoon's far end into a container below its rim, hold it there and lift it out.

## When to use

A held utensil must go into a container briefly (taste, wet).

## Not to be confused with

- `stir`: stir circles inside the container; dip goes in and out once.

## Inputs

- `tool` (`tool_ref`): The held utensil.
- `container` (`container_ref`): The pot or bowl.

## Call

Send one JSON object:

```json
{"contract": "dip", "args": {"tool": "<tool>", "container": "<container>"}}
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

- `dipped(container=$container)` — A held utensil tip entered the container below its rim and came back out.
- `holding(hand=right, object=$tool)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

