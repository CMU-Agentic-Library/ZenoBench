# contract_015 — Close an articulated door or drawer

Close one annotated articulated target and verify its joint position.

Paired SkillNode: `skill_007`. Status: `representative_runs_only`.

## Inputs

- `articulated`: articulated_ref

## Preconditions

- `articulated_annotated` — contract_precheck
- `closure_path_clear` — policy_attempt

## Planner action predicate

`close_articulated_joint(articulated)` — reported only after the measured state facts pass.

## Measured postconditions

- `joint_closed` — contract_runner

## Grounded noun slots

- `articulated`: `articulated`; constraints `{'source': 'rig.ann', 'required': True}`

## Policy paths

### powered_microwave

Match before execution: `[{'noun': 'articulated', 'field': 'powered_microwave', 'equals': True}]`.

1. `policy_025` with ['articulated']

### manual_handle

Match before execution: `[{'noun': 'articulated', 'field': 'has_handle', 'equals': True}]`.

1. `policy_023` with ['articulated']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_005` / `auto`.
