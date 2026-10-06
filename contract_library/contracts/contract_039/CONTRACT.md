# contract_039 — Lower torso for floor reach

Lower the robot torso to its configured minimum before floor interaction.

Paired SkillNode: `skill_031`. Status: `representative_runs_only`.

## Inputs


## Preconditions

- `joint_path_clear` — policy_attempt

## Planner action predicate

`lower_torso()` — reported only after the measured state facts pass.

## Measured postconditions

- `posture_at_target` — contract_runner

## Grounded noun slots


## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_005` with []


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_008` / `lower`.
