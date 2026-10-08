# contract_020 — Inspect a receptacle

Look into a container, a cabinet, an appliance cavity or onto a support and report the objects inside or on it. A closed cabinet is opened for the look and closed again.

Paired SkillNode: `skill_012` (`inspect-receptacle`).

## Precheck

- [all paths] `base_near(place=$receptacle)` — GT: base_pose, scene_annotation
- [path closed_cabinet] `hand_empty(hand=right)` — GT: gripper_state

## Verifier

- [all paths] `observed(target=$receptacle)` — GT: robot_memory

## Policy paths

- `closed_cabinet` when receptacle.kind == 'articulated' and not receptacle.is_open: `policy_003()` -> `policy_062($receptacle)` -> `policy_088($receptacle)` -> `policy_003()` -> `policy_063($receptacle)`
- `open_view` when always: `policy_088($receptacle)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
