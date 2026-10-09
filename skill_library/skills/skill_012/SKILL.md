---
name: inspect-receptacle
description: Look into a container, a cabinet, an appliance cavity or onto a support and report the objects inside or on it. A closed cabinet is opened for the look and closed again.
---

# Inspect a receptacle (`inspect`)

`inspect(receptacle: entity_ref)`

Look into a container, a cabinet, an appliance cavity or onto a support and report the objects inside or on it. A closed cabinet is opened for the look and closed again.

## When to use

The contents of a container or cabinet must be seen (opens it if needed).

## Not to be confused with

- `look`: look reports nothing about contents.
- `search`: inspect examines one given receptacle; search chooses where to look.

## Inputs

- `receptacle` (`entity_ref`): Container, articulated cabinet/appliance or support to examine.

## Outputs

- `contents` (`object_list`): Objects found inside/on the receptacle and visible.

## Call

Send one JSON object:

```json
{"contract": "inspect", "args": {"receptacle": "<entity>"}}
```

Argument formats:

- `entity_ref`: any annotated object, support, articulated part or button

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires base_near(place=$receptacle). Some bound nouns add preconditions (see Conditions that depend on the bound nouns).

## Preconditions (checked before moving)

- `base_near(place=$receptacle)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).

## Postconditions (checked after the action)

- `observed(target=$receptacle)` — The robot saw the target in its head camera during this episode (set by look, search, inspect, explore).

## Conditions that depend on the bound nouns

- when receptacle.kind == 'articulated' and not receptacle.is_open: needs `hand_empty(hand=right)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

