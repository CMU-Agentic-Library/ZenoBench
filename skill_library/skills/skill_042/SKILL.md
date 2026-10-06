---
name: back-away-while-carrying
description: Reverse the base while preserving the right-hand grasp.
---

# Back away while carrying (skill_042)

## When to use

Reverse the base while preserving the right-hand grasp.

## Inputs

- `object` (`object_ref`): The object currently held in the right hand.
- `distance_m` (`positive_number`): Requested backward travel distance in metres.

## Preconditions

- `held_by_right_hand` — `policy_attempt`
- `backward_path_clear` — `policy_attempt`

## Planner action predicate

`retreat_carried_object(object, distance_m)` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['base_backed_off', 'grasp_preserved']`.

## Expected state change

- `base_backed_off` — measured by `contract_runner`
- `grasp_preserved` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_042` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_050", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_right_held': True}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_035(distance_m)`


Verifier: `back_off`.

## Related Skills

- `skill_002` (`preparation`) when a load needs clearance from furniture before travel — Back away, then select a new travel pose.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

One back away while carrying attempt on the grounded scene state.

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
