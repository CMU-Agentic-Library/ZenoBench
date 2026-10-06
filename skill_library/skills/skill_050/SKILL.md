---
name: clear-microwave-door-sweep
description: Move the robot to the microwave hinge clearance pose and verify a fresh clearance event.
---

# Clear microwave door sweep (skill_050)

## When to use

Move the robot to the microwave hinge clearance pose and verify a fresh clearance event.

## Inputs

- `articulated` (`articulated_ref`): Grounded powered microwave door.

## Preconditions

- `microwave_annotated` — `contract_precheck`
- `clearance_path_open` — `policy_attempt`

## Planner action predicate

`clear_microwave_door_sweep(articulated)` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['microwave_sweep_clear']`.

## Expected state change

- `microwave_sweep_clear` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_050` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_058", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `articulated`: `articulated`; constraints `{'source': 'rig.ann', 'required': True, 'category_equals': 'microwave', 'required_annotation': 'door_button'}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_030(articulated)`


Verifier: `microwave_clear`.

## Related Skills

- `skill_023` (`preparation`) when microwave door sweep is clear and powered opening is next — Measured clearance permits hinge motion.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

One clear microwave door sweep attempt on grounded scene state.

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
