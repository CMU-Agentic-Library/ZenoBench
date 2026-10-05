# contract_009 — Navigate empty-handed

Move the empty-handed robot base to one target pose.

Paired SkillNode: `skill_001`. Status: `representative_runs_only`.

## Inputs

- `pose`: pose2d

## Preconditions

- `target_navigable` — policy_attempt
- `carried_object_matches_state` — not_enforced

## Measured postconditions

- `base_at` — contract_runner

## Grounded noun slots


## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_001` with ['pose']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_001` / `empty`.
