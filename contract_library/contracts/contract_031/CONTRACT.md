# contract_031 — Open powered microwave door

Open the annotated powered microwave door and measure its joint.

Paired SkillNode: `skill_023`. Status: `representative_runs_only`.

## Inputs

- `appliance`: appliance_ref

## Preconditions

- `right_hand_empty` — policy_attempt
- `target_annotated` — policy_attempt

## Measured postconditions

- `joint_open_enough` — contract_runner

## Grounded noun slots

- `appliance`: `articulated`; constraints `{'source': 'rig.ann', 'required': True, 'category_equals': 'microwave', 'required_annotation': 'door_button'}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_024` with ['appliance']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_004` / `powered`.
