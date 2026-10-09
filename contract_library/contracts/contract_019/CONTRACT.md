# contract_019 — Look at a target

Aim the head camera at a target (turning the base if it is outside the head yaw range) and record every annotated object in view as observed.

Verb: `look`.

## Precheck

- none

## Verifier

- [all paths] `in_view(target=$target)` — GT: base_pose, head_joints, head_fk, collision_model
- [all paths] `observed(target=$target)` — GT: robot_memory

## Policy paths

- `head_only` when target.bearing_abs_deg <= 55: `policy_068($target)`
- `turn_then_head` when always: `policy_066($target)` -> `policy_068($target)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
