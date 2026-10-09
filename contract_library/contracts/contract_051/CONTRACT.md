# contract_051 — Heat food

Bring food to a target temperature with an appliance and switch the heat off: in the closed microwave (start key + wait) or in a pot on the stove burner (power key on, wait, power key off).

Verb: `heat`.

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [all paths] `base_near(place=$appliance)` — GT: base_pose, scene_annotation
- [path microwave] `in_appliance(object=$food, appliance=$appliance)` — GT: object_pose, appliance_annotation
- [path microwave] `is_closed(articulated=$appliance)` — GT: articulation_joint, articulation_annotation
- [path stove_pot] `in_cookware_on_burner(food=$food, appliance=$appliance)` — GT: object_pose, container_profile, appliance_annotation

## Verifier

- [all paths] `temperature_at_least(object=$food, temp_c=$temp_c)` — GT: thermal_state
- [all paths] `not heating(appliance=$appliance)` — GT: thermal_state

## Policy paths

- `microwave` when appliance.category == 'microwave': `policy_032($appliance)` -> `policy_064($food, $temp_c)`
- `stove_pot` when appliance.category == 'stove': `policy_094(@appliance.power_button, state=True)` -> `policy_090($food, $temp_c, $appliance)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
