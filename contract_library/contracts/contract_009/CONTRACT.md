# contract_009 — Navigate to a place

Drive the holonomic base to a free stand-off pose next to a room, piece of furniture, support, articulated part or object. The arm is tucked when empty, or held in the compact carry pose with the load.

Verb: `navigate`.

## Precheck

- none

## Verifier

- [all paths] `base_near(place=$destination)` — GT: base_pose, scene_annotation

## Policy paths

- `two_hand_carry` when robot.both_hold_same: `policy_097($destination) as plan` -> `policy_058(@robot.right_object, #plan.pose)`
- `carry` when robot.right_held: `policy_097($destination) as plan` -> `policy_002(#plan.pose, name=@robot.right_object, min_bottom_z=#plan.carry_bottom_z)`
- `empty` when always: `policy_097($destination) as plan` -> `policy_001(#plan.pose)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
