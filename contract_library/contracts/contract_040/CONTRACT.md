# contract_040 — Raise torso for work surface

Raise the robot torso to its configured maximum.

Paired SkillNode: `skill_032`. Status: `representative_runs_only`.

## Inputs


## Preconditions

- `joint_path_clear` — policy_attempt

## Planner action predicate

`raise_torso()` — reported only after the measured state facts pass.

## Measured postconditions

- `posture_at_target` — contract_runner

## Grounded noun slots


## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_006` with []


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_008` / `raise`.
