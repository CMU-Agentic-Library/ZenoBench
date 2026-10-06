---
name: pick-an-object
description: Grasp and lift one annotated scene object with the right hand.
---

# Pick an object (skill_004)

## When to use

Grasp and lift one annotated scene object with the right hand.

## Inputs

- `object` (`object_ref`): The object to pick.

## Preconditions

- `right_hand_empty` — `contract_precheck`
- `object_annotated` — `contract_noun_binding`
- `object_reachable` — `policy_attempt`

## Planner action predicate

`acquire_object(object)` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['held_by_right_hand', 'object_lifted']`.

## Expected state change

- `held_by_right_hand` — measured by `contract_runner`
- `object_lifted` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_004` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_012", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True}`

### Policy path: microwave_cavity

Match before execution: `[{'noun': 'object', 'field': 'location', 'equals': 'microwave_cavity'}]`.

1. `policy_048(object)`

### Policy path: floor_corner

Match before execution: `[{'noun': 'object', 'field': 'on_floor', 'equals': True}, {'noun': 'object', 'field': 'grasp_types', 'contains': 'edge_pinch_after_push'}]`.

1. `policy_014(object)`

### Policy path: rectangular_rim

Match before execution: `[{'noun': 'object', 'field': 'grasp_types', 'contains': 'rim_pinch_rect'}]`.

1. `policy_012(object)`

### Policy path: round_rim

Match before execution: `[{'noun': 'object', 'field': 'grasp_types', 'contains': 'rim_pinch'}]`.

1. `policy_011(object)`

### Policy path: top_pinch

Match before execution: `[{'noun': 'object', 'field': 'grasp_types', 'contains': 'top_pinch'}]`.

1. `policy_010(object)`

### Policy path: flat_edge

Match before execution: `[{'noun': 'object', 'field': 'on_floor', 'equals': False}, {'noun': 'object', 'field': 'grasp_types', 'contains': 'edge_pinch_after_push'}]`.

1. `policy_013(object)`

### Policy path: handle_only

Match before execution: `[{'noun': 'object', 'field': 'grasp_types', 'contains': 'handle_pinch'}, {'noun': 'object', 'field': 'handle_collider', 'equals': True}]`.

1. `policy_055(object)`


Verifier: `contract_002 / auto`.

## Related Skills

- `skill_026` (`follows`) when an object was removed and the manual access must be closed — Restore the door or drawer to its measured closed joint.
- `skill_005` (`enables`) when the task requires the grasped object on a support — Right-hand holding is the place precondition.
- `skill_006` (`enables`) when the task requires the grasped object inside a container — Right-hand holding is the container-place precondition.
- `skill_037` (`enables`) when the task requires the object upright on a support — Orient before release, then verify upright after placement.
- `skill_038` (`enables`) when the task requires a target area on a support — A held object can be placed near an xy hint.
- `skill_039` (`enables`) when the task requires both upright and near-hint placement — Both final predicates are checked after release.
- May follow `skill_025` (`enables`) when the target object is enclosed by a closed manual door or drawer.
- May follow `skill_018` (`recovery`) when moving pick failed and the object is stationary and reachable.
- May follow `skill_027` (`alternative`) when top pinch geometry is absent or fails but another grasp exists.
- May follow `skill_047` (`enables`) when object lies behind the opened hinged door.
- May follow `skill_048` (`enables`) when object lies inside the opened drawer.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.
- Conditional fallback `skill_016` when object remains on an annotated support edge and right hand is empty: edge-specific grasp may be appropriate

## Scope and evidence

one planner-visible pick attempt

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the task goal
- Outside scope: guaranteeing reachability before execution
- Outside scope: placing or transporting the object to a destination
