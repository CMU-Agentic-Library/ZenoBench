---
name: pick-object
description: Grasp one object with the right gripper and lift it. The grasp is chosen automatically from the object and where it is: from inside a microwave, slide-to-edge + edge pinch for flat items, handle pinch, rectangular or round rim pinch, top pinch, or a two-handed lift for wide items.
---

# Pick an object (`pick`)

`pick(object: object_ref, hands: hand?, grasp: tag?, pass_by: pose2d?)`

Grasp one object with the right gripper and lift it. The grasp is chosen automatically from the object and where it is: from inside a microwave, slide-to-edge + edge pinch for flat items, handle pinch, rectangular or round rim pinch, top pinch, or a two-handed lift for wide items.

## When to use

The robot must hold an object for any later hand action.

## Not to be confused with

- `regrasp`: regrasp improves a grasp on an object that is already held.
- `uncover`: uncover lifts a lid off its container and keeps it.
- `fetch`: fetch also navigates and places.

## Inputs

- `object` (`object_ref`): The object to grasp.
- `hands` (`hand`, optional, one of 'right', 'both'): "both" requests a two-handed lift for wide items.
- `grasp` (`tag`, optional, one of 'handle', 'rim', 'top', 'edge'): Optional grasp style to request: handle, rim, top or edge.
- `pass_by` (`pose2d`, optional): Optional base waypoint: grasp while driving past.

## Outputs

- `grasp` (`hand`): Grasp route actually used.
- `lift_m` (`number`): Measured lift of the object.

## Call

Send one JSON object:

```json
{"contract": "pick", "args": {"object": "<object>"}}
```

Argument formats:

- `hand`: "right" or "left"
- `object_ref`: a movable annotated scene object
- `pose2d`: a base pose [x, y, yaw_deg] in metres and degrees
- `tag`: an asset tag or asset name, e.g. "fruit", "toy", "cherry_tomato"

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires hand_empty(hand=right); base_near(place=$object). Some bound nouns add preconditions (see Conditions that depend on the bound nouns).

## Preconditions (checked before moving)

- `hand_empty(hand=right)` — The given gripper holds nothing.
- `base_near(place=$object)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).

## Postconditions (checked after the action)

- `holding(hand=right, object=$object)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.

## Conditions that depend on the bound nouns

- when object.location == 'microwave_cavity': needs `is_open(articulated=@object.appliance)`
- when object.location in ['refrigerator', 'cabinet']: needs `is_open(articulated=@object.appliance)`
- when args.pass_by and 'top_pinch' in object.grasp_types: needs `grasp_clearance(object=$object)`
- when args.hands == 'both' and object.wide_box: needs `hand_empty(hand=left)`; ensures `holding(hand=left, object=$object)`
- when args.hands == 'both' and object.flat: needs `hand_empty(hand=left)`; ensures `holding(hand=left, object=$object)`
- when 'rim_pinch' in object.grasp_types: needs `grasp_clearance(object=$object)`
- when 'top_pinch' in object.grasp_types: needs `grasp_clearance(object=$object)`

## May invalidate

`on($object,*)`, `inside($object,*)`, `on_top_of($object,*)`, `on_floor($object)`, `hand_empty(right)`, `grasp_clearance($object)`, `edge_overhang($object)`, `at_initial_place($object)`, `arm_stowed(right)`, `in_appliance($object,*)`, `on_burner($object,*)`, `covered(*,$object)`

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

- no reachable grasp from any base pose
- object not held after lift (slipped)
- no free support edge for a flat object
