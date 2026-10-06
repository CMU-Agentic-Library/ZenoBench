# contract_010 — Navigate while carrying

Move the base while preserving the current right-hand grasp.

Paired SkillNode: `skill_002`. Status: `representative_runs_only`.

## Inputs

- `object`: object_ref
- `pose`: pose2d

## Preconditions

- `target_navigable` — policy_attempt
- `carried_object_matches_state` — not_enforced

## Planner action predicate

`transport_carried_object(object, pose)` — reported only after the measured state facts pass.

## Measured postconditions

- `base_at` — contract_runner
- `grasp_preserved` — contract_runner

## Grounded noun slots

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_right_held': True}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_002` with ['pose']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_001` / `carry`.
