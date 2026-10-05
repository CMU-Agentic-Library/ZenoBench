---
name: skill_010
description: Press the start button and verify that heating became active.
---

# skill_010 — Start microwave heating

## When to use

Press the start button and verify that heating became active.

## Inputs

- `appliance` (`appliance_ref`): appliance

## Preconditions

- `right_hand_empty` — `contract_precheck`
- `button_reachable` — `policy_attempt`
- `start_conditions` — `policy_attempt`

## Expected state change

- `button_pressed_this_call` — measured by `contract_runner`
- `heating_active` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_010` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_018", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `appliance`: `articulated`; constraints `{'source': 'rig.ann', 'required': True, 'category_equals': 'microwave', 'required_annotation': 'start_button'}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_027(appliance, button=start)`
2. `policy_028(appliance, button=start)`
3. `policy_029(appliance, button=start)`


Verifier: `contract_007 / start`.

## Related Skills

- `skill_040` (`enables`) when heating was started but target temperature is unmet — The thermal wait advances the live model and verifies the threshold.
- May follow `skill_024` (`enables`) when configured food is inside the microwave.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

one start-button press

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
