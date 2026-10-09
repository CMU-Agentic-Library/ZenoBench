# contract_033 — Rotate a held object

Turn the held object about the vertical axis by the requested angle (e.g. align a book's spine).

Verb: `rotate`.

## Precheck

- [all paths] `holding(hand=right, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk

## Verifier

- [all paths] `yaw_rotated(object=$object, degrees=$degrees)` — GT: object_pose (before/after)
- [all paths] `holding(hand=right, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk

## Policy paths

- `wrist_yaw` when always: `policy_075($object, $degrees)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
