# contract_046 — Stir a container

Dip a held spoon's far end into a container and move it in a circle below the rim; succeeds after one full turn inside.

Verb: `stir`.

## Precheck

- [all paths] `holding(hand=right, object=$tool)` — GT: gripper_state, finger_joints, object_pose, arm_fk
- [all paths] `base_near(place=$container)` — GT: base_pose, scene_annotation
- [all paths] `uncovered(container=$container)` — GT: object_pose, container_profile, asset_tags

## Verifier

- [all paths] `stirred(container=$container)` — GT: robot_memory (tool-tip samples)
- [all paths] `holding(hand=right, object=$tool)` — GT: gripper_state, finger_joints, object_pose, arm_fk

## Policy paths

- `circle_below_rim` when 'utensil' in tool.tags: `policy_085($tool, $container)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
