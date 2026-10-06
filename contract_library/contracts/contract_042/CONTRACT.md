# contract_042 — Straighten waist

Return the waist pitch to neutral.

Paired SkillNode: `skill_034`. Status: `representative_runs_only`.

## Inputs


## Preconditions

- `joint_path_clear` — policy_attempt

## Planner action predicate

`straighten_waist()` — reported only after the measured state facts pass.

## Measured postconditions

- `posture_at_target` — contract_runner

## Grounded noun slots


## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_009` with []


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_008` / `straighten`.
