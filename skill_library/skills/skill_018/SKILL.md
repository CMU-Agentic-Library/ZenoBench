---
name: skill_018
description: Attempt one right-hand pick during a base move to a target pose.
---

# skill_018 — Pick while the base moves

## When to use

Attempt one right-hand pick during a base move to a target pose.

## Inputs

- `object` (`object_ref`): object
- `base_path` (`pose2d`): base path

## Preconditions

- `right_hand_empty` — `contract_precheck`
- `object_annotated` — `policy_attempt`
- `object_reachable` — `policy_attempt`

## Expected state change

- `held_by_right_hand` — measured by `contract_runner`
- `object_lifted` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_018` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_026", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_052(object, base_path)`


Verifier: `contract_002 / moving`.

## Related Skills

- `skill_004` (`recovery`) when moving pick failed and the object is stationary and reachable — Retry through a stationary grasp only after fresh observation.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.
- Conditional fallback `skill_004` when object remains reachable and base motion has stopped: stationary pick is an alternative to mobile pick

## Scope and evidence

one synchronized moving pick

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
