---
name: open-a-hinged-door
description: Open a manual revolute door and read back its hinge joint.
---

# Open a hinged door (skill_047)

## When to use

Open a manual revolute door and read back its hinge joint.

## Inputs

- `articulated` (`articulated_ref`): The uniquely grounded door or drawer.

## Preconditions

- `right_hand_empty` — `policy_attempt`
- `target_annotated` — `policy_attempt`

## Planner action predicate

`unfold_hinged_door(articulated)` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['joint_open_enough']`.

## Expected state change

- `joint_open_enough` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_047` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_055", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `articulated`: `articulated`; constraints `{'source': 'rig.ann', 'required': True, 'required_annotation': 'handle', 'forbid_annotation': 'door_button', 'requires_joint_type': 'revolute'}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_049(articulated)`


Verifier: `contract_004 / handle`.

## Related Skills

- `skill_004` (`enables`) when object lies behind the opened hinged door — Access permits a grounded pick attempt.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

One open a hinged door attempt on grounded scene state.

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
