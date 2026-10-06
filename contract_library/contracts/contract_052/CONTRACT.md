# contract_052 — Translate base locally

Move an empty, tucked robot along a short local forward axis and measure displacement.

Paired SkillNode: `skill_044`. Status: `representative_runs_only`.

## Inputs

- `forward_m`: number

## Preconditions

- `right_hand_empty` — policy_attempt
- `arm_tucked` — policy_attempt
- `straight_path_clear` — policy_attempt

## Planner action predicate

`translate_base(forward_m)` — reported only after the measured state facts pass.

## Measured postconditions

- `base_translated_locally` — contract_runner

## Grounded noun slots


## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_037` with ['forward_m']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: custom `base_translate`.
