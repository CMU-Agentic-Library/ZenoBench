# contract_077 — Dip a utensil

Lower a held spoon's far end into a container below its rim, hold it there and lift it out.

Paired SkillNode: `skill_069` (`dip-utensil`).

## Precheck

- [all paths] `holding(hand=right, object=$tool)` — GT: gripper_state, finger_joints, object_pose, arm_fk
- [all paths] `base_near(place=$container)` — GT: base_pose, scene_annotation
- [all paths] `uncovered(container=$container)` — GT: object_pose, container_profile, asset_tags

## Verifier

- [all paths] `dipped(container=$container)` — GT: robot_memory (tool-tip samples)
- [all paths] `holding(hand=right, object=$tool)` — GT: gripper_state, finger_joints, object_pose, arm_fk

## Policy paths

- `tip_below_rim` when 'utensil' in tool.tags: `policy_113($tool, $container)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
