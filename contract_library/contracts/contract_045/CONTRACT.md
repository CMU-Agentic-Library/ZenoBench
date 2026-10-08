# contract_045 — Wipe a surface

Press a held sponge on a support and sweep a 30 cm strip twice; succeeds when the sponge stayed in contact over at least half of the strip.

Paired SkillNode: `skill_037` (`wipe-surface`).

## Precheck

- [all paths] `holding(hand=right, object=$tool)` — GT: gripper_state, finger_joints, object_pose, arm_fk
- [all paths] `base_near(place=$surface)` — GT: base_pose, scene_annotation

## Verifier

- [all paths] `wiped(support=$surface)` — GT: robot_memory (tool-bottom contact samples)
- [all paths] `holding(hand=right, object=$tool)` — GT: gripper_state, finger_joints, object_pose, arm_fk

## Policy paths

- `sponge_strip` when 'wiping_tool' in tool.tags: `policy_084($tool, $surface)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
