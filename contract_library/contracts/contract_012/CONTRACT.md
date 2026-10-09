# contract_012 — Retreat from an obstacle

Back the base straight away from a piece of furniture, appliance or object until it is at least the given distance away; a held load stays held.

Verb: `retreat`.

## Precheck

- none

## Verifier

- [all paths] `base_clear_of(place=$obstacle, distance_m=$distance_m)` — GT: base_pose, scene_annotation

## Policy paths

- `microwave_door_sweep` when obstacle.instance == 'kitchen_microwave': `policy_030($obstacle)`
- `bimanual_or_left_load` when robot.left_held: `policy_067($obstacle, $distance_m)`
- `loaded` when robot.right_held: `policy_035($distance_m)`
- `empty` when always: `policy_100($obstacle, $distance_m) as plan` -> `policy_037(#plan.forward_m)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
