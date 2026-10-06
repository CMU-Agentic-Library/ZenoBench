---
name: pick-a-cup-by-its-handle
description: Attempt one handle grasp of a cup and verify grasp and lift.
---

# Pick a cup by its handle (skill_017)

## When to use

Attempt one handle grasp of a cup and verify grasp and lift.

## Inputs

- `object` (`object_ref`): object

## Preconditions

- `right_hand_empty` — `contract_precheck`
- `object_annotated` — `policy_attempt`
- `object_reachable` — `policy_attempt`
- `handle_collision_body_prepared` — `not_enforced`

## Planner action predicate

`grip_cup_handle(object)` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['held_by_right_hand', 'object_lifted']`.

## Expected state change

- `held_by_right_hand` — measured by `contract_runner`
- `object_lifted` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_017` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_025", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_grasp_type': 'handle_pinch'}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_055(object)`


Verifier: `contract_002 / cup_handle`.

## Related Skills

- May follow `skill_028` (`alternative`) when round-rim grasp fails and the cup has an annotated handle.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

one cup-handle pick

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
