# contract_036 — Flip a flat object over

Turn a flat object upside down where it lies: slide it to an edge, pinch the overhang, lift, roll the hand 180 deg, lay it back and release.

Verb: `flip`.

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [all paths] `base_near(place=$object)` — GT: base_pose, scene_annotation

## Verifier

- [all paths] `flipped(object=$object)` — GT: object_pose (before/after)
- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Policy paths

- `edge_roll` when object.flat: `policy_045($object)` -> `policy_013($object)` -> `policy_078($object)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
