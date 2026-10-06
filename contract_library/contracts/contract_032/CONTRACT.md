# contract_032 — Close powered microwave door

Close the annotated powered microwave door and measure its joint.

Paired SkillNode: `skill_024`. Status: `representative_runs_only`.

## Inputs

- `appliance`: appliance_ref

## Preconditions

- `right_hand_empty` — policy_attempt
- `target_annotated` — policy_attempt

## Planner action predicate

`shut_microwave_door(appliance)` — reported only after the measured state facts pass.

## Measured postconditions

- `joint_closed` — contract_runner

## Grounded noun slots

- `appliance`: `articulated`; constraints `{'source': 'rig.ann', 'required': True, 'category_equals': 'microwave', 'required_annotation': 'door_button'}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_025` with ['appliance']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_005` / `powered`.
