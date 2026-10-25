# contract_022 — Explore a room

Cover a room from up to six viewpoints with a left/centre/right head sweep both ways; succeeds when at least 75 % of the room's furniture was seen. A piece of furniture counts once one of its support layers (top or shelf) is in view; seeing every shelf of one piece is explore_furniture.

Paired SkillNode: `skill_014` (`explore-room`).

## Precheck

- none

## Verifier

- [all paths] `room_explored(room=$room)` — GT: robot_memory, room_annotation

## Policy paths

- `viewpoints` when always: `policy_069($room)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
