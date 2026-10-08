# contract_038 — Pull an object closer

Drag an object toward the robot with the pads pressed on its top until it is within reach (e.g. from the back of a deep counter); if the pads slide over a round or slippery top, the fingers hook the far side and push it toward the robot.

Paired SkillNode: `skill_030` (`pull-object`).

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [all paths] `base_near(place=$object)` — GT: base_pose, scene_annotation

## Verifier

- [all paths] `moved_toward_base(object=$object, distance_m=$distance_m)` — GT: object_pose (before/after), base_pose
- [all paths] `reachable(target=$object)` — GT: base_pose, arm_ik, collision_model, object_pose, grasp_annotation

## Policy paths

- `top_drag` when always: `policy_041()` -> `policy_079($object, $distance_m)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
