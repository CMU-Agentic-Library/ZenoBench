# contract_070 — Shake a held object

Oscillate the held object sideways three times (settle or loosen contents) while keeping the grasp.

Verb: `shake`.

## Precheck

- [all paths] `holding(hand=right, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk

## Verifier

- [all paths] `shaken(object=$object)` — GT: robot_memory (TCP oscillation + hold checks)
- [all paths] `holding(hand=right, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk

## Policy paths

- `lateral` when always: `policy_102($object)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
