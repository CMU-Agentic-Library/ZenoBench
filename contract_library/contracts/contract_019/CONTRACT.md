# contract_019 — Tuck the right arm

Move the right arm into the measured travel posture.

Paired SkillNode: `skill_011`. Status: `representative_runs_only`.

## Inputs


## Preconditions

- `right_hand_empty` — policy_attempt
- `target_within_joint_limits` — policy_attempt
- `collision_free_motion` — policy_attempt

## Measured postconditions

- `posture_at_target` — contract_runner

## Grounded noun slots


## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_003` with []


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_008` / `tuck`.
