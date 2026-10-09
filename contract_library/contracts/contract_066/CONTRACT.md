# contract_066 — Measure an object

Look at an object and report its current axis-aligned size.

Verb: `measure`.

## Precheck

- none

## Verifier

- [all paths] `measured(object=$object)` — GT: robot_memory, asset_annotation, object_pose
- [all paths] `in_view(target=$object)` — GT: base_pose, head_joints, head_fk, collision_model

## Policy paths

- `look_and_size` when always: `policy_111($object)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
