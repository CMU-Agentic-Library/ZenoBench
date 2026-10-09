# contract_017 — Tuck an arm

Fold an empty arm to its travel posture along a collision-checked path.

Verb: `tuck`.

## Precheck

- [all paths] `hand_empty(hand=$hand)` — GT: gripper_state

## Verifier

- [all paths] `arm_stowed(hand=$hand)` — GT: arm_joints

## Policy paths

- `left` when args.hand == 'left': `policy_091()`
- `right` when always: `policy_003()`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
