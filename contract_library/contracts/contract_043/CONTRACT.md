# contract_043 — Tip an object over

Push a standing tall object near its top so it falls onto its side on the same support (lays down a carton or bottle that is too tall to top-pinch).

Verb: `tip`.

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [all paths] `base_near(place=$object)` — GT: base_pose, scene_annotation
- [all paths] `upright(object=$object)` — GT: object_pose

## Verifier

- [all paths] `lying(object=$object)` — GT: object_pose, asset_annotation

## Policy paths

- `push_high` when object.tall: `policy_082($object)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
