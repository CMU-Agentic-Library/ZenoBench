# contract_017 — Press the appliance door button

Physically press one annotated appliance door button.

Paired SkillNode: `skill_009`. Status: `representative_runs_only`.

## Inputs

- `appliance`: appliance_ref

## Preconditions

- `right_hand_empty` — contract_precheck
- `button_reachable` — policy_attempt
- `start_conditions` — policy_attempt

## Planner action predicate

`press_appliance_door_button(appliance)` — reported only after the measured state facts pass.

## Measured postconditions

- `button_pressed_this_call` — contract_runner

## Grounded noun slots

- `appliance`: `articulated`; constraints `{'source': 'rig.ann', 'required': True, 'category_equals': 'microwave', 'required_annotation': 'door_button'}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_027` with ['appliance']
2. `policy_028` with ['appliance']
3. `policy_029` with ['appliance']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_007` / `auto`.
