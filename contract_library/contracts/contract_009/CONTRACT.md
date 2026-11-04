# contract_009 — Navigate to a place

Drive the holonomic base to a free stand-off pose next to a room, piece of furniture, support, articulated part or object. An empty arm is tucked and hangs at the side (inside the base footprint) while the base drives, then returns to the tuck; a loaded one is held in the compact carry pose.

Paired SkillNode: `skill_001` (`navigate-place`).

## Precheck

- none

## Verifier

- [all paths] `base_near(place=$destination)` — GT: base_pose, scene_annotation

## Policy paths

- `two_hand_carry` when robot.both_hold_same: `policy_097($destination) as plan` -> `policy_058(@robot.right_object, #plan.pose)`
- `drive` when always: `policy_092($destination)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
