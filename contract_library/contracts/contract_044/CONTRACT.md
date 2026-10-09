# contract_044 — Stand an object upright

Make a lying object stand: pinch it, rotate its local up axis to vertical in the hand, and set it down upright on the same support.

Paired SkillNode: `skill_036` (`upright-object`).

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [all paths] `base_near(place=$object)` — GT: base_pose, scene_annotation
- [all paths] `lying(object=$object)` — GT: object_pose, asset_annotation

## Verifier

- [all paths] `upright(object=$object)` — GT: object_pose
- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [path pick_orient_place] `on(object=$object, support=@object.support)` — GT: object_pose, asset_annotation, support_annotation

## Policy paths

- `pick_orient_place` when 'top_pinch' in object.grasp_types: `policy_010($object)` -> `policy_054($object, max_tilt_deg=15.0)` -> `policy_015($object, @object.support, hint=@object.xy)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
