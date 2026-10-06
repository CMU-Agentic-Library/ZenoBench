# contract_029 — Carry a large object with both hands

Move a currently two-hand-held object to one base pose.

Paired SkillNode: `skill_021`. Status: `experimental_callable`.

## Inputs

- `object`: object_ref
- `pose`: pose2d

## Preconditions

- `target_navigable` — policy_attempt
- `carried_object_matches_state` — not_enforced
- `two_hand_hold` — not_enforced

## Planner action predicate

`convoy_bimanual_load(object, pose)` — reported only after the measured state facts pass.

## Measured postconditions

- `base_at` — contract_runner
- `grasp_preserved` — contract_runner

## Grounded noun slots

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_058` with ['object', 'pose']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_001` / `two_hand_carry`.
