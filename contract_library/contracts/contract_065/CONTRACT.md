# contract_065 — Identify an object

Look at an object and report its category and tags (asset annotation) once it is in the head camera view.

Paired SkillNode: `skill_057` (`identify-object`).

## Precheck

- none

## Verifier

- [all paths] `identified(object=$object)` — GT: robot_memory, asset_annotation
- [all paths] `in_view(target=$object)` — GT: base_pose, head_joints, head_fk, collision_model

## Policy paths

- `look_and_label` when always: `policy_110($object)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
