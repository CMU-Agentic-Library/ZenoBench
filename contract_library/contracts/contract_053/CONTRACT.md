# contract_053 — Cover a container with a lid

Lay the held lid centred on the container rim (within 3 cm, tilt <= 12 deg) and release it.

Paired SkillNode: `skill_045` (`cover-container`).

## Precheck

- [all paths] `holding(hand=right, object=$lid)` — GT: gripper_state, finger_joints, object_pose, arm_fk
- [all paths] `base_near(place=$container)` — GT: base_pose, scene_annotation
- [all paths] `uncovered(container=$container)` — GT: object_pose, container_profile, asset_tags

## Verifier

- [all paths] `covered(container=$container, lid=$lid)` — GT: object_pose, container_profile
- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Policy paths

- `rim_plane` when lid.is_lid: `policy_087($lid, $container)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
