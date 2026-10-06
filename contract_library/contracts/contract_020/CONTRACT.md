# contract_020 — Set torso height

Move the torso lift to one requested joint height.

Paired SkillNode: `skill_012`. Status: `representative_runs_only`.

## Inputs

- `height_m`: number

## Preconditions

- `right_hand_empty` — policy_attempt
- `target_within_joint_limits` — policy_attempt
- `collision_free_motion` — policy_attempt

## Planner action predicate

`set_torso_height(height_m)` — reported only after the measured state facts pass.

## Measured postconditions

- `posture_at_target` — contract_runner

## Grounded noun slots


## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_004` with ['height_m']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_008` / `torso`.
