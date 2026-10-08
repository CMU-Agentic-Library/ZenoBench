# contract_022 — Explore a room

Cover a room from up to three viewpoints with a left/centre/right head sweep; succeeds when at least 75 % of the room's supports and objects were seen.

Paired SkillNode: `skill_014` (`explore-room`).

## Precheck

- none

## Verifier

- [all paths] `room_explored(room=$room)` — GT: robot_memory, room_annotation

## Policy paths

- `viewpoints` when always: `policy_069($room)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
