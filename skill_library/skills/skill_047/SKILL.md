---
name: fetch-object
description: Bring one object to a support or container: the robot goes to the object, picks it up, carries it to the receptacle and puts it there.
---

# Fetch an object to a receptacle (`fetch`)

`fetch(object: object_ref, receptacle: receptacle_ref)`

Bring one object to a support or container: the robot goes to the object, picks it up, carries it to the receptacle and puts it there.

## When to use

One object must be brought to a destination (navigate, pick, carry, place in one node).

## Not to be confused with

- `restore`: restore's destination is the object's starting support.
- `collect`: collect moves a list into one container.
- `pick`: fetch also carries and places the object.

## Inputs

- `object` (`object_ref`): What to bring.
- `receptacle` (`receptacle_ref`): Destination support or open container.

## Call

Send one JSON object:

```json
{"contract": "fetch", "args": {"object": "<object>", "receptacle": "<receptacle>"}}
```

Argument formats:

- `object_ref`: a movable annotated scene object
- `receptacle_ref`: a support surface or an open container

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires hand_empty(hand=right). Some bound nouns add preconditions (see Conditions that depend on the bound nouns).

## Preconditions (checked before moving)

- `hand_empty(hand=right)` — The given gripper holds nothing.

## Postconditions (checked after the action)

- `hand_empty(hand=right)` — The given gripper holds nothing.

## Conditions that depend on the bound nouns

- when receptacle.kind == 'object': needs `uncovered(container=$receptacle)`; ensures `inside(object=$object, container=$receptacle)`
- when receptacle.kind == 'support': ensures `on(object=$object, support=$receptacle)`

## May invalidate

`on($object,*)`, `inside($object,*)`, `at_initial_place($object)`, `base_near(*)`, `reachable(*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

