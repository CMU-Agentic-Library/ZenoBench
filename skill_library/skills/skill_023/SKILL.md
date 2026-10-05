---
name: skill_023
description: Open the annotated powered microwave door and measure its joint.
---

# skill_023 — Open powered microwave door

## When to use

Open the annotated powered microwave door and measure its joint.

## Inputs

- `appliance` (`appliance_ref`): The grounded microwave appliance.

## Preconditions

- `right_hand_empty` — `policy_attempt`
- `target_annotated` — `policy_attempt`

## Expected state change

- `joint_open_enough` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_023` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_031", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `appliance`: `articulated`; constraints `{'source': 'rig.ann', 'required': True, 'category_equals': 'microwave', 'required_annotation': 'door_button'}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_024(appliance)`


Verifier: `contract_004 / powered`.

## Related Skills

- `skill_014` (`enables`) when microwave cavity must be opened before loading — Open joint makes the cavity physically accessible.
- `skill_015` (`enables`) when food must be retrieved from a closed microwave — Open joint makes the cavity physically accessible.
- `skill_024` (`follows`) when microwave inspection is complete without retrieval — Close the open door to satisfy the terminal closed condition.
- May follow `skill_040` (`follows`) when heated food must be removed for serving.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

One open powered microwave door attempt on the grounded scene state.

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
