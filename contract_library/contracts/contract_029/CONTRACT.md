# contract_029 — Release an object

Open one gripper where the object already rests (e.g. let go of a braced pot, or of an object that was set down by another action) and back the fingers off.

Verb: `release`.

## Precheck

- [all paths] `holding(hand=$hand, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk

## Verifier

- [all paths] `hand_empty(hand=$hand)` — GT: gripper_state

## Policy paths

- `open_in_place` when always: `policy_096($object, $hand)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
