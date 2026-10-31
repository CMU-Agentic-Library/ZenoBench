# contract_036 — Flip a flat object over

Turn a flat object upside down on its support: slide it to an edge, pinch the overhang, swing the pinched edge up and over the far edge until the object passes vertical, release, and push it over. It lands on its other face about one object-length further onto the support, so that much free room is needed.

Paired SkillNode: `skill_028` (`flip-object`).

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [all paths] `base_near(place=$object)` — GT: base_pose, scene_annotation

## Verifier

- [all paths] `flipped(object=$object)` — GT: object_pose (before/after)
- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Policy paths

- `edge_roll` when object.flat: `policy_045($object)` -> `policy_013($object)` -> `policy_078($object)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
