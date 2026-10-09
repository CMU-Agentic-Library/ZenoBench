# contract_042 — Roll a cylinder

Roll a lying constant-radius cylinder (rolling pin, can on its side) along its support by pressing on its top; the object must rotate, not slide. A bottle with a neck rolls in an arc around the neck and is not a valid noun.

Verb: `roll`.

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [all paths] `base_near(place=$object)` — GT: base_pose, scene_annotation
- [all paths] `lying(object=$object)` — GT: object_pose, asset_annotation

## Verifier

- [all paths] `object_rolled(object=$object)` — GT: object_pose (before/after)

## Policy paths

- `push_above_axis` when always: `policy_081($object, $distance_m)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
