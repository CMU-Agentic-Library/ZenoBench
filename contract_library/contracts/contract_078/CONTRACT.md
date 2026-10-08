# contract_078 — Hide an object

Make an object invisible from outside: put it into a container and cover that container with its lid, or put it on a shelf inside a cabinet and close the cabinet.

Paired SkillNode: `skill_070` (`hide-object`).

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [path container_with_lid] `uncovered(container=$receptacle)` — GT: object_pose, container_profile, asset_tags

## Verifier

- [all paths] `hidden(object=$object)` — GT: object_pose, container_profile, articulation_joint, support_annotation
- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Policy paths

- `container_with_lid` when receptacle.kind == 'object' and args.lid: `[fetch](object=$object, receptacle=$receptacle)` -> `[navigate](destination=$lid)` -> `[pick](object=$lid)` -> `[navigate](destination=$receptacle)` -> `[cover](container=$receptacle, lid=$lid)`
- `closed_cabinet` when receptacle.kind == 'support' and receptacle.category == 'cabinet_inside': `[navigate](destination=@receptacle.appliance)` -> `[open](articulated=@receptacle.appliance)` -> `[fetch](object=$object, receptacle=$receptacle)` -> `[close](articulated=@receptacle.appliance)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
