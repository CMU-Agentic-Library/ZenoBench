# contract_011 — Open an articulated door or drawer

Open one annotated articulated target and verify its joint position.

Paired SkillNode: `skill_003`. Status: `representative_runs_only`.

## Inputs

- `articulated`: articulated_ref

## Preconditions

- `articulated_annotated` — contract_precheck
- `opening_route_feasible` — policy_attempt

## Measured postconditions

- `joint_open_enough` — contract_runner

## Grounded noun slots

- `articulated`: `articulated`; constraints `{'source': 'rig.ann', 'required': True}`

## Policy paths

### powered_microwave

Match before execution: `[{'noun': 'articulated', 'field': 'powered_microwave', 'equals': True}]`.

1. `policy_024` with ['articulated']

### manual_drawer

Match before execution: `[{'noun': 'articulated', 'field': 'type', 'equals': 'prismatic'}, {'noun': 'articulated', 'field': 'has_handle', 'equals': True}]`.

1. `policy_050` with ['articulated']

### manual_hinged_door

Match before execution: `[{'noun': 'articulated', 'field': 'type', 'equals': 'revolute'}, {'noun': 'articulated', 'field': 'has_handle', 'equals': True}]`.

1. `policy_049` with ['articulated']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_004` / `auto`.
