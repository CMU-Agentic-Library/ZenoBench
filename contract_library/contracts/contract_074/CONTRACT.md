# contract_074 — Knock on a door

Tap a closed door or drawer panel twice with the closed fingertips beside its handle; the panel must stay closed.

Paired SkillNode: `skill_066` (`knock-articulated`).

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [all paths] `base_near(place=$articulated)` — GT: base_pose, scene_annotation
- [all paths] `is_closed(articulated=$articulated)` — GT: articulation_joint, articulation_annotation

## Verifier

- [all paths] `knocked(articulated=$articulated)` — GT: event_log (fingertip contact), articulation_joint
- [all paths] `is_closed(articulated=$articulated)` — GT: articulation_joint, articulation_annotation

## Policy paths

- `panel_taps` when articulated.has_handle: `policy_106($articulated)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
