# contract_051 — Pivot base in place

Rotate an empty, tucked robot by a bounded signed angle and verify its new yaw.

Paired SkillNode: `skill_043`. Status: `representative_runs_only`.

## Inputs

- `delta_yaw_deg`: number

## Preconditions

- `right_hand_empty` — policy_attempt
- `arm_tucked` — policy_attempt
- `turn_arc_clear` — policy_attempt

## Planner action predicate

`pivot_base(delta_yaw_deg)` — reported only after the measured state facts pass.

## Measured postconditions

- `base_yaw_changed` — contract_runner

## Grounded noun slots


## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_036` with ['delta_yaw_deg']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: custom `base_rotate`.
