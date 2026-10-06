---
name: pick-by-rectangular-rim
description: Grasp a rectangular tray or box by its annotated rim.
---

# Pick by rectangular rim (skill_029)

## When to use

Grasp a rectangular tray or box by its annotated rim.

## Inputs

- `object` (`object_ref`): The uniquely grounded scene object.

## Preconditions

- `right_hand_empty` — `contract_precheck`
- `target_annotated` — `policy_attempt`

## Planner action predicate

`clasp_rectangular_rim(object)` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['held_by_right_hand', 'object_lifted']`.

## Expected state change

- `held_by_right_hand` — measured by `contract_runner`
- `object_lifted` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_029` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_037", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_grasp_type': 'rim_pinch_rect'}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_012(object)`


Verifier: `contract_002 / rect_rim`.

## Related Skills

- `skill_006` (`enables`) when a rectangular-rim container was grasped for relocation — Relocate the held container before loading objects into it.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

One pick by rectangular rim attempt on the grounded scene state.

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
