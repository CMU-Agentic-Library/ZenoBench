# contract_067 — Count objects of a category

Sweep the head from the current place and count the visible objects whose asset or tag matches.

Paired SkillNode: `skill_059` (`count-category`).

## Precheck

- none

## Verifier

- [all paths] `counted(category=$category)` — GT: robot_memory, head_fk

## Policy paths

- `head_sweep` when always: `policy_112($category)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
