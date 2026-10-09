# contract_010 — Approach a manipulation target

Park the base where the right arm has a collision-free IK solution at the target's reach pose: 10 cm above an object or support, the handle pre-grasp of a door or drawer, 8 cm in front of a button.

Verb: `approach`.

## Precheck

- [all paths] `base_near(place=$target)` — GT: base_pose, scene_annotation

## Verifier

- [all paths] `reachable(target=$target)` — GT: base_pose, arm_ik, collision_model, object_pose, grasp_annotation

## Policy paths

- `reach_on_the_move` when args.pass_by: `policy_098($target) as reach` -> `policy_051(#reach.position, #reach.rotation, $pass_by)`
- `park` when always: `policy_065($target)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
