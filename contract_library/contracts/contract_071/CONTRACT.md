# contract_071 — Hover a held object over a target

Hold the carried object 6 cm above a target without releasing it, e.g. to show or to align before a drop: above a container's opening, a support's centre, a burner, or a door's handle.

Paired SkillNode: `skill_063` (`hover-object`).

## Precheck

- [all paths] `holding(hand=right, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk
- [all paths] `base_near(place=$target)` — GT: base_pose, scene_annotation

## Verifier

- [all paths] `hovering_over(object=$object, target=$target)` — GT: object_pose, gripper_state, asset_annotation
- [all paths] `holding(hand=right, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk

## Policy paths

- `above_target` when always: `policy_115($object, $target)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
