---
name: place-object
description: Put the right-held object down on a support surface or into an open container and release it. How it is put down is chosen automatically from the receptacle and grasp: into a microwave (insert, release, withdraw), into a container, an edge-held flat object slid back over an edge, onto an ordinary surface (optionally near a hint point), or while driving past.
---

# Place a held object (`place`)

`place(object: object_ref, receptacle: receptacle_ref, hint_xy: xy?, pass_by: pose2d?)`

Put the right-held object down on a support surface or into an open container and release it. How it is put down is chosen automatically from the receptacle and grasp: into a microwave (insert, release, withdraw), into a container, an edge-held flat object slid back over an edge, onto an ordinary surface (optionally near a hint point), or while driving past.

## When to use

A held object must end up resting on a support, in a container or on a burner.

## Not to be confused with

- `drop`: drop releases above a container opening without lowering.
- `stack`: stack targets another object's top face.
- `release`: release opens the fingers where the object already rests.

## Inputs

- `object` (`object_ref`): The held object.
- `receptacle` (`receptacle_ref`): A support surface or an open container.
- `hint_xy` (`xy`, optional): Optional preferred position on a surface.
- `pass_by` (`pose2d`, optional): Optional base waypoint: place while driving past.

## Outputs

- `position` (`xy`): Measured bottom position after release.

## Call

Send one JSON object:

```json
{"contract": "place", "args": {"object": "<object>", "receptacle": "<receptacle>"}}
```

Argument formats:

- `object_ref`: a movable annotated scene object
- `pose2d`: a base pose [x, y, yaw_deg] in metres and degrees
- `receptacle_ref`: a support surface or an open container
- `xy`: a world position [x, y] in metres

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires holding(hand=right, object=$object); base_near(place=$receptacle). Some bound nouns add preconditions (see Conditions that depend on the bound nouns).

## Preconditions (checked before moving)

- `holding(hand=right, object=$object)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.
- `base_near(place=$receptacle)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).

## Postconditions (checked after the action)

- `hand_empty(hand=right)` — The given gripper holds nothing.

## Conditions that depend on the bound nouns

- when receptacle.kind == 'support' and receptacle.is_microwave_cavity and robot.right_kind == 'pinch': needs `is_open(articulated=kitchen_microwave)`; ensures `on(object=$object, support=$receptacle)`; ensures `in_appliance(object=$object, appliance=kitchen_microwave)`
- when receptacle.kind == 'support' and receptacle.is_microwave_cavity: needs `is_open(articulated=kitchen_microwave)`; ensures `on(object=$object, support=$receptacle)`; ensures `in_appliance(object=$object, appliance=kitchen_microwave)`
- when receptacle.kind == 'support' and receptacle.category == 'cabinet_inside' and receptacle.appliance: needs `is_open(articulated=@receptacle.appliance)`; ensures `on(object=$object, support=$receptacle)`
- when receptacle.kind == 'object': needs `uncovered(container=$receptacle)`; ensures `inside(object=$object, container=$receptacle)`
- when receptacle.kind == 'support' and args.pass_by: ensures `on(object=$object, support=$receptacle)`
- when receptacle.kind == 'support' and robot.right_kind == 'edge': ensures `on(object=$object, support=$receptacle)`
- when receptacle.kind == 'support' and receptacle.category == 'cooktop': ensures `on(object=$object, support=$receptacle)`; ensures `on_burner(object=$object, appliance=@receptacle.appliance)`
- when receptacle.kind == 'support': ensures `on(object=$object, support=$receptacle)`

## May invalidate

`holding(right,$object)`, `presenting($object)`, `base_clear_of(*)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

- target unreachable
- container shifted before release
- object not on/in target after release
