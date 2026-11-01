# contract_017 — Tuck an arm

Fold an empty arm to its travel posture: hanging straight down at the side, inside the base footprint. The right fold also raises the torso and straightens the waist (the travel posture includes them); the left fold moves only the left arm. A loaded arm is not folded: navigate carries the load in its carry pose.

Paired SkillNode: `skill_009` (`tuck-arm`).

## Precheck

- [all paths] `hand_empty(hand=$hand)` — GT: gripper_state

## Verifier

- [all paths] `arm_stowed(hand=$hand)` — GT: arm_joints

## Policy paths

- `left` when args.hand == 'left': `policy_091()`
- `right` when always: `policy_003()`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
