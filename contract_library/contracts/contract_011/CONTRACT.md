# contract_011 — Face a target

Rotate the base in place until it faces the target (heading error <= 20 deg).

Paired SkillNode: `skill_003` (`face-target`).

## Precheck

- none

## Verifier

- [all paths] `facing(target=$target)` — GT: base_pose, scene_annotation

## Policy paths

- `already_facing` when target.bearing_abs_deg <= 2: 
- `rotate` when always: `policy_066($target)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
