# contract_039 — Expose a grasp edge

Push a flat object (book, plate, notebook) until it overhangs a free support edge by >= 5.5 cm while its centre of mass stays on the support, so the overhang can be pinched.

Paired SkillNode: `skill_031` (`expose-object`).

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [all paths] `base_near(place=$object)` — GT: base_pose, scene_annotation

## Verifier

- [all paths] `edge_overhang(object=$object)` — GT: object_pose, asset_annotation, support_annotation

## Policy paths

- `slide_to_edge` when object.flat: `policy_045($object)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
