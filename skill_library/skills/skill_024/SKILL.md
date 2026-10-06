---
name: close-powered-microwave-door
description: Close the annotated powered microwave door and measure its joint.
---

# Close powered microwave door (skill_024)

## When to use

Close the annotated powered microwave door and measure its joint.

## Inputs

- `appliance` (`appliance_ref`): The grounded microwave appliance.

## Preconditions

- `right_hand_empty` — `policy_attempt`
- `target_annotated` — `policy_attempt`

## Planner action predicate

`shut_microwave_door(appliance)` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['joint_closed']`.

## Expected state change

- `joint_closed` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_024` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_032", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `appliance`: `articulated`; constraints `{'source': 'rig.ann', 'required': True, 'category_equals': 'microwave', 'required_annotation': 'door_button'}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_025(appliance)`


Verifier: `contract_005 / powered`.

## Related Skills

- `skill_010` (`enables`) when configured food is inside the microwave — Start requires a closed microwave door.
- May follow `skill_014` (`follows`) when microwave food is loaded and heating is next.
- May follow `skill_023` (`follows`) when microwave inspection is complete without retrieval.
- May follow `skill_007` (`alternative`) when a powered microwave door must close.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

One close powered microwave door attempt on the grounded scene state.

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
