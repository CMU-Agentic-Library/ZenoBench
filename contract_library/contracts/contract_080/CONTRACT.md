# contract_080 — Mark free spots on a support

Show where the held object can go on a support surface: see the surface clearly from one or two stand-off poses (one where the robot stands when it does about as well; a long table: one view per half), standing up with the head aimed at it, and number up to twelve free spots on those head images, one set of numbers over all of them: one beside each object on the surface first, then another side of each, then open space. Every spot fits the object at any turn with room left to its neighbours and is in view. The numbered images come with the next observation (one images entry per view, overlay "place_spots" and view k); disc n is spots[n-1] on every image it is drawn on. Nothing is placed: place the object with place(object, receptacle=support, hint_xy=<the chosen spot's xy>).

Paired SkillNode: `skill_072` (`mark-spots-support`).

## Precheck

- [all paths] `holding(hand=right, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk

## Verifier

- [all paths] `in_view(target=$support)` — GT: base_pose, head_joints, head_fk, collision_model

## Policy paths

- `view_and_mark` when always: `policy_117($support)` -> `policy_118($object, $support)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
