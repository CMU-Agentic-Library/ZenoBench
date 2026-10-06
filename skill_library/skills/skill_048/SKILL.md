---
name: extend-a-drawer
description: Open a manual prismatic drawer and read back its sliding joint.
---

# Extend a drawer (skill_048)

## When to use

Open a manual prismatic drawer and read back its sliding joint.

## Inputs

- `articulated` (`articulated_ref`): The uniquely grounded door or drawer.

## Preconditions

- `right_hand_empty` — `policy_attempt`
- `target_annotated` — `policy_attempt`

## Planner action predicate

`extend_drawer(articulated)` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['joint_open_enough']`.

## Expected state change

- `joint_open_enough` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_048` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_056", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `articulated`: `articulated`; constraints `{'source': 'rig.ann', 'required': True, 'required_annotation': 'handle', 'forbid_annotation': 'door_button', 'requires_joint_type': 'prismatic'}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_050(articulated)`


Verifier: `contract_004 / handle`.

## Related Skills

- `skill_004` (`enables`) when object lies inside the opened drawer — Access permits a grounded pick attempt.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

One extend a drawer attempt on grounded scene state.

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
