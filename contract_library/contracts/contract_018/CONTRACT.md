# contract_018 — Start microwave heating

Press the start button and verify that heating became active.

Paired SkillNode: `skill_010`. Status: `representative_runs_only`.

## Inputs

- `appliance`: appliance_ref

## Preconditions

- `right_hand_empty` — contract_precheck
- `button_reachable` — policy_attempt
- `start_conditions` — policy_attempt

## Planner action predicate

`start_microwave_heating(appliance)` — reported only after the measured state facts pass.

## Measured postconditions

- `button_pressed_this_call` — contract_runner
- `heating_active` — contract_runner

## Grounded noun slots

- `appliance`: `articulated`; constraints `{'source': 'rig.ann', 'required': True, 'category_equals': 'microwave', 'required_annotation': 'start_button'}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_027` with ['appliance']
2. `policy_028` with ['appliance']
3. `policy_029` with ['appliance']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_007` / `start`.
