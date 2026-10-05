# contract_021 — Set waist pitch

Move the waist to one requested pitch angle in radians.

Paired SkillNode: `skill_013`. Status: `representative_runs_only`.

## Inputs

- `pitch_rad`: number

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

1. `policy_007` with ['pitch_rad']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_008` / `waist`.
