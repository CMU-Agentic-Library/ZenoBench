---
name: skill_020
description: Attempt one floor-corner grasp and verify right-hand lift.
---

# skill_020 — Pick a flat object from a floor corner

## When to use

Attempt one floor-corner grasp and verify right-hand lift.

## Inputs

- `object` (`object_ref`): object

## Preconditions

- `right_hand_empty` — `contract_precheck`
- `object_annotated` — `policy_attempt`
- `object_reachable` — `policy_attempt`

## Expected state change

- `held_by_right_hand` — measured by `contract_runner`
- `object_lifted` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_020` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_028", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_grasp_type': 'edge_pinch_after_push'}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_014(object)`


Verifier: `contract_002 / floor_corner`.

## Related Skills

- `skill_005` (`enables`) when a floor object was lifted and needs a support — Place the recovered object after observing the grasp.
- May follow `skill_031` (`preparation`) when a flat object lies on the floor and is hard to reach.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

one floor-corner pick

Availability: `experimental_callable`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
