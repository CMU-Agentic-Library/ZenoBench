---
name: navigate-while-carrying
description: Move the base while preserving the current right-hand grasp.
---

# Navigate while carrying (skill_002)

## When to use

Move the base while preserving the current right-hand grasp.

## Inputs

- `object` (`object_ref`): The object currently held in the right hand.
- `pose` (`pose2d`): pose

## Preconditions

- `target_navigable` — `policy_attempt`
- `carried_object_matches_state` — `not_enforced`

## Planner action predicate

`transport_carried_object(object, pose)` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['base_at', 'grasp_preserved']`.

## Expected state change

- `base_at` — measured by `contract_runner`
- `grasp_preserved` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_002` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_010", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_right_held': True}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_002(pose, name=object)`


Verifier: `contract_001 / carry`.

## Related Skills

- May follow `skill_041` (`preparation`) when a carried object needs height clearance before travel.
- May follow `skill_042` (`preparation`) when a load needs clearance from furniture before travel.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

one loaded base move

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
