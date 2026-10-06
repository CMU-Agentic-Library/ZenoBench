---
name: pick-a-flat-object-at-an-edge
description: Attempt one edge grasp of a flat object and verify grasp and lift.
---

# Pick a flat object at an edge (skill_016)

## When to use

Attempt one edge grasp of a flat object and verify grasp and lift.

## Inputs

- `object` (`object_ref`): object

## Preconditions

- `right_hand_empty` — `contract_precheck`
- `object_annotated` — `policy_attempt`
- `object_reachable` — `policy_attempt`

## Planner action predicate

`pinch_flat_object_edge(object)` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['held_by_right_hand', 'object_lifted']`.

## Expected state change

- `held_by_right_hand` — measured by `contract_runner`
- `object_lifted` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_016` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_024", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_grasp_type': 'edge_pinch_after_push'}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_013(object)`


Verifier: `contract_002 / edge`.

## Related Skills

- `skill_030` (`enables`) when the flat object is edge-held and must be placed on a shelf — Edge placement matches the grasp mode.
- May follow `skill_035` (`preparation`) when a flat object needs a graspable support overhang.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

one edge-route pick

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
