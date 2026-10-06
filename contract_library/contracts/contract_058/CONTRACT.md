# contract_058 — Clear microwave door sweep

Move the robot to the microwave hinge clearance pose and verify a fresh clearance event.

Paired SkillNode: `skill_050`. Status: `representative_runs_only`.

## Inputs

- `articulated`: articulated_ref

## Preconditions

- `microwave_annotated` — contract_precheck
- `clearance_path_open` — policy_attempt

## Planner action predicate

`clear_microwave_door_sweep(articulated)` — reported only after the measured state facts pass.

## Measured postconditions

- `microwave_sweep_clear` — contract_runner

## Grounded noun slots

- `articulated`: `articulated`; constraints `{'source': 'rig.ann', 'required': True, 'category_equals': 'microwave', 'required_annotation': 'door_button'}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_030` with ['articulated']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: custom `microwave_clear`.
