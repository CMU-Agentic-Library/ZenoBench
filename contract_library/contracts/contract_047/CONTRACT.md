# contract_047 — Pour contents into a container

Hold the cup's far lip over a container, turn the cup about that lip up to 90 deg and return it upright; succeeds when at least half of the loose items that were in the cup are inside the target. A rim-held cup tilts away from the pinch; a handle-held cup rolls sideways about the forearm.

Verb: `pour`.

## Precheck

- [all paths] `holding(hand=right, object=$source)` — GT: gripper_state, finger_joints, object_pose, arm_fk
- [all paths] `base_near(place=$target)` — GT: base_pose, scene_annotation
- [all paths] `uncovered(container=$target)` — GT: object_pose, container_profile, asset_tags
- [all paths] `not container_empty(container=$source)` — GT: object_pose, container_profile

## Verifier

- [all paths] `poured_into(source=$source, target=$target)` — GT: object_pose (before/after), container_profile
- [all paths] `holding(hand=right, object=$source)` — GT: gripper_state, finger_joints, object_pose, arm_fk

## Policy paths

- `tilt_over_rim` when source.is_container: `policy_086($source, $target)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
