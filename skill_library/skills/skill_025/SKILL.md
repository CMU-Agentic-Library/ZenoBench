---
name: skill_025
description: Open one handle-operated door or drawer.
---

# skill_025 — Open a manual handle

## When to use

Open one handle-operated door or drawer.

## Inputs

- `articulated` (`articulated_ref`): The uniquely grounded door or drawer.

## Preconditions

- `right_hand_empty` — `policy_attempt`
- `target_annotated` — `policy_attempt`

## Expected state change

- `joint_open_enough` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_025` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_033", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `articulated`: `articulated`; constraints `{'source': 'rig.ann', 'required': True, 'required_annotation': 'handle', 'forbid_annotation': 'door_button'}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_022(articulated)`


Verifier: `contract_004 / handle`.

## Related Skills

- `skill_004` (`enables`) when the target object is enclosed by a closed manual door or drawer — Open access before attempting a general pick.
- May follow `skill_003` (`alternative`) when a manual door must use an explicit handle route.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

One open a manual handle attempt on the grounded scene state.

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
