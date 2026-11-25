# contract_018 — Reset the posture

Return to the home posture: arm folded, torso up, waist straight -- the tuck, raise and straighten skills in turn. Used to recover from an unknown arm state.

Paired SkillNode: `skill_010` (`reset-posture`).

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Verifier

- [all paths] `arm_stowed(hand=right)` — GT: arm_joints
- [all paths] `torso_raised()` — GT: torso_joint
- [all paths] `waist_straight()` — GT: waist_joint

## Policy paths

- `joint_home` when always: `policy_003()` -> `policy_006()` -> `policy_009()`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
