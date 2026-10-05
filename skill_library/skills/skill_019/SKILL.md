---
name: skill_019
description: Release one right-held object onto a support during a base move.
---

# skill_019 — Place on a support while the base moves

## When to use

Release one right-held object onto a support during a base move.

## Inputs

- `object` (`object_ref`): object
- `support` (`support_ref`): support
- `base_path` (`pose2d`): base path

## Preconditions

- `held_by_right_hand` — `contract_precheck`
- `target_annotated` — `policy_attempt`
- `target_accessible` — `policy_attempt`

## Expected state change

- `on` — measured by `contract_runner`
- `right_hand_empty` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_019` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_027", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_right_held': True}`
- `support`: `support`; constraints `{'source': 'rig.ann', 'required': True}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_053(object, support, base_path)`


Verifier: `contract_003 / moving`.

## Related Skills

- `skill_005` (`recovery`) when moving place failed and the object remains right-held — Try stationary support placement after fresh observation.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.
- Conditional fallback `skill_005` when object remains right-held and base motion has stopped: stationary support placement is an alternative to mobile placement

## Scope and evidence

one synchronized moving placement

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
