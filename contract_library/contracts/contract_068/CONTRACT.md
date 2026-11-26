# contract_068 — Wave the hand

Raise an empty hand at head height and swing it (greeting / attention gesture); either hand, the one that reaches the wave best.

Paired SkillNode: `skill_060` (`wave-hand`).

## Precheck

- [all paths] `hand_empty(hand=any)` — GT: gripper_state

## Verifier

- [all paths] `waved()` — GT: robot_memory (TCP swing samples)
- [all paths] `hand_empty(hand=any)` — GT: gripper_state

## Policy paths

- `raised_swing` when always: `policy_104()`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
