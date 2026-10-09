# contract_076 — Stop an appliance

Switch an appliance's heat off: press the stove power key off, or open the microwave door, which ends its cycle.

Verb: `stop`.

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [all paths] `base_near(place=$appliance)` — GT: base_pose, scene_annotation

## Verifier

- [all paths] `not heating(appliance=$appliance)` — GT: thermal_state
- [path microwave_door] `is_open(articulated=$appliance)` — GT: articulation_joint, articulation_annotation

## Policy paths

- `stove_key_off` when appliance.category == 'stove': `policy_094(@appliance.power_button, state=False)`
- `microwave_door` when appliance.category == 'microwave': `policy_024($appliance)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
