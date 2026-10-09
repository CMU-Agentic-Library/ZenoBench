# contract_054 — Uncover a container

Lift the lid off a container by its knob and set it down beside the container: on the same support when it has room, else on the nearest counter-height support; the lid noun is found from GT (the lid resting on the rim).

Verb: `uncover`.

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [all paths] `base_near(place=$container)` — GT: base_pose, scene_annotation

## Verifier

- [all paths] `uncovered(container=$container)` — GT: object_pose, container_profile, asset_tags
- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [path knob_lift_aside] `on(object=@container.lid, support=@container.aside_support)` — GT: object_pose, asset_annotation, support_annotation

## Policy paths

- `knob_lift_aside` when container.lid: `policy_010(@container.lid)` -> `policy_015(@container.lid, @container.aside_support)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
