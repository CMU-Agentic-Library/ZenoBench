# contract_027 — Drop an object into a container

Hold the object 5 cm above a container's opening, centred, and let go; the object falls in.

Verb: `drop`.

## Precheck

- [all paths] `holding(hand=right, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk
- [all paths] `base_near(place=$container)` — GT: base_pose, scene_annotation
- [all paths] `uncovered(container=$container)` — GT: object_pose, container_profile, asset_tags

## Verifier

- [all paths] `inside(object=$object, container=$container)` — GT: object_pose, container_profile
- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Policy paths

- `above_opening` when always: `policy_073($object, $container)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
