# contract_052 — Chill food

Keep food in the closed refrigerator until it is at or below a target temperature.

Verb: `chill`.

## Precheck

- [all paths] `in_appliance(object=$food, appliance=$appliance)` — GT: object_pose, appliance_annotation
- [all paths] `is_closed(articulated=$appliance)` — GT: articulation_joint, articulation_annotation

## Verifier

- [all paths] `temperature_at_most(object=$food, temp_c=$temp_c)` — GT: thermal_state

## Policy paths

- `fridge_wait` when appliance.category == 'refrigerator': `policy_089($food, $temp_c, $appliance)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
