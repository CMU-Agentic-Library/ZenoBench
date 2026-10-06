# contract_033 — Open a manual handle

Open one handle-operated door or drawer.

Paired SkillNode: `skill_025`. Status: `representative_runs_only`.

## Inputs

- `articulated`: articulated_ref

## Preconditions

- `right_hand_empty` — policy_attempt
- `target_annotated` — policy_attempt

## Planner action predicate

`pull_manual_handle(articulated)` — reported only after the measured state facts pass.

## Measured postconditions

- `joint_open_enough` — contract_runner

## Grounded noun slots

- `articulated`: `articulated`; constraints `{'source': 'rig.ann', 'required': True, 'required_annotation': 'handle', 'forbid_annotation': 'door_button'}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_022` with ['articulated']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_004` / `handle`.
