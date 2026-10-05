---
name: skill_041
description: Lift a right-held object until its bottom clears a required height.
---

# skill_041 — Raise carried object for clearance

## When to use

Lift a right-held object until its bottom clears a required height.

## Inputs

- `object` (`object_ref`): The object currently held in the right hand.
- `min_bottom_z` (`positive_number`): Required minimum world z of the held object bottom.

## Preconditions

- `held_by_right_hand` — `policy_attempt`

## Expected state change

- `held_object_above_height` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_041` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_049", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_right_held': True}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_034(min_bottom_z)`


Verifier: `carry_height`.

## Related Skills

- `skill_002` (`preparation`) when a carried object needs height clearance before travel — Raise the load before using the carry-navigation policy.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

One raise carried object for clearance attempt on the grounded scene state.

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
