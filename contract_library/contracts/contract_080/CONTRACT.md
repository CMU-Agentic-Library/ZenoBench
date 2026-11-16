# contract_080 — Mark free spots on a support

Show where the held object can go on a support surface: drive to a stand-off pose from which the whole surface is in one head camera frame (the pose the robot stands at is kept when it already is), aim the head at it, and number up to six spread-out free spots on that head image. Every spot fits the object at any turn with room left to its neighbours and is in view. The numbered image comes with the next observation (images entry with overlay "place_spots"); disc n is spots[n-1]. Nothing is placed: place the object with place(object, receptacle=support, hint_xy=<the chosen spot's xy>).

Paired SkillNode: `skill_072` (`mark-spots-support`).

## Precheck

- [all paths] `holding(hand=right, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk

## Verifier

- [all paths] `in_view(target=$support)` — GT: base_pose, head_joints, head_fk, collision_model

## Policy paths

- `view_and_mark` when always: `policy_117($support)` -> `policy_118($object, $support)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
