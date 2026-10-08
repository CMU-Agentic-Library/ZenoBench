# contract_062 — Swap two objects

Exchange the positions of two objects on their supports via a free buffer spot.

Paired SkillNode: `skill_054` (`swap-objects`).

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Verifier

- [all paths] `positions_swapped(a=$a, b=$b)` — GT: object_pose (before/after)
- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Policy paths

- `via_buffer` when always: `[navigate](destination=$a)` -> `[pick](object=$a)` -> `[place](object=$a, receptacle=@a.support, hint_xy=@a.buffer_xy)` -> `[navigate](destination=$b)` -> `[pick](object=$b)` -> `[navigate](destination=@a.support)` -> `[place](object=$b, receptacle=@a.support, hint_xy=@a.xy)` -> `[navigate](destination=$a)` -> `[pick](object=$a)` -> `[navigate](destination=@b.support)` -> `[place](object=$a, receptacle=@b.support, hint_xy=@b.xy)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
