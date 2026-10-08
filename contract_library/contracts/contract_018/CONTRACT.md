# contract_018 — Reset the posture

Return to the home posture: fingers open, arm folded, torso up, waist straight, by a collision-checked joint-space move. Used to recover from an unknown arm state.

Paired SkillNode: `skill_010` (`reset-posture`).

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Verifier

- [all paths] `arm_stowed(hand=right)` — GT: arm_joints
- [all paths] `torso_raised()` — GT: torso_joint
- [all paths] `waist_straight()` — GT: waist_joint

## Policy paths

- `joint_home` when always: `policy_040()` -> `policy_003()` -> `policy_095() as home` -> `policy_039(#home.target)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
