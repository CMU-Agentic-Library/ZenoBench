---
name: expose-a-flat-object-edge
description: Push a flat object to a measured, graspable support overhang.
---

# Expose a flat object edge (skill_035)

## When to use

Push a flat object to a measured, graspable support overhang.

## Inputs

- `object` (`object_ref`): The uniquely grounded scene object.

## Preconditions

- `right_hand_empty` — `contract_precheck`
- `object_on_annotated_support` — `policy_attempt`
- `free_support_edge` — `policy_attempt`

## Planner action predicate

`expose_flat_object_edge(object)` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['edge_overhang_ready']`.

## Expected state change

- `edge_overhang_ready` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_035` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_043", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_grasp_type': 'edge_pinch_after_push'}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_045(object)`


Verifier: `edge_ready`.

## Related Skills

- `skill_016` (`preparation`) when a flat object needs a graspable support overhang — The edge exposure step verifies the overhang before the edge pick.
- May follow `skill_045` (`recovery`) when rear contact could not make required progress on a flat object.
- May follow `skill_046` (`recovery`) when top drag could not make required progress on a flat object.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

One expose a flat object edge attempt on the grounded scene state.

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
