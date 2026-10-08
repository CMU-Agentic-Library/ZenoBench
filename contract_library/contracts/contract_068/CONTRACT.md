# contract_068 — Wave the hand

Raise the empty right hand at head height and swing it (greeting / attention gesture).

Paired SkillNode: `skill_060` (`wave-hand`).

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Verifier

- [all paths] `waved()` — GT: robot_memory (TCP swing samples)
- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Policy paths

- `raised_swing` when always: `policy_104()`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
