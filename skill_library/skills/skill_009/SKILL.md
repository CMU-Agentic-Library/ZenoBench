---
name: press-the-appliance-door-button
description: Physically press one annotated appliance door button.
---

# Press the appliance door button (skill_009)

## When to use

Physically press one annotated appliance door button.

## Inputs

- `appliance` (`appliance_ref`): appliance

## Preconditions

- `right_hand_empty` — `contract_precheck`
- `button_reachable` — `policy_attempt`
- `start_conditions` — `policy_attempt`

## Planner action predicate

`press_appliance_door_button(appliance)` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['button_pressed_this_call']`.

## Expected state change

- `button_pressed_this_call` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_009` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_017", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `appliance`: `articulated`; constraints `{'source': 'rig.ann', 'required': True, 'category_equals': 'microwave', 'required_annotation': 'door_button'}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_027(appliance, button=door)`
2. `policy_028(appliance, button=door)`
3. `policy_029(appliance, button=door)`


Verifier: `contract_007 / auto`.

## Related Skills

- No fixed relation; select the next node from the task goal and observation.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

one door-button press

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
