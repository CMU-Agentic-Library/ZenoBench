# contract_034 — Regrasp a held object

Set the held object down on a support and grasp it again with a fresh, centred grasp (recovery when the object has pivoted in the pinch).

Verb: `regrasp`.

## Precheck

- [all paths] `holding(hand=right, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk
- [all paths] `base_near(place=$support)` — GT: base_pose, scene_annotation

## Verifier

- [all paths] `holding(hand=right, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk

## Policy paths

- `set_down_and_pick` when always: `policy_076($object, $support)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
