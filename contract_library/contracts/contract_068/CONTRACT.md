# contract_068 — Wave the hand

Raise the empty right hand at head height and swing it (greeting / attention gesture).

Verb: `wave`.

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Verifier

- [all paths] `waved()` — GT: robot_memory (TCP swing samples)
- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Policy paths

- `raised_swing` when always: `policy_104()`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
