# contract_037 — Push an object

Slide an object along its support in a direction with closed fingers: from behind when there is room, or by pressing on its top and dragging when it stands against a wall or closed edge.

Verb: `push`.

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [all paths] `base_near(place=$object)` — GT: base_pose, scene_annotation

## Verifier

- [all paths] `object_moved(object=$object, direction_xy=$direction_xy, distance_m=$distance_m)` — GT: object_pose (before/after)

## Policy paths

- `drag_from_top` when object.near_closed_edge: `policy_041()` -> `policy_044($object, @object.support, $direction_xy, $distance_m)`
- `thin_auto` when object.flat: `policy_026($object, @object.support, $direction_xy, $distance_m)`
- `from_behind` when always: `policy_041()` -> `policy_043($object, @object.support, $direction_xy, $distance_m)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
