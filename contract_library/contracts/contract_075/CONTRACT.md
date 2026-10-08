# contract_075 — Sweep objects together

Push several objects on one support toward their centroid until they form a cluster (radius 12 cm), without grasping them.

Paired SkillNode: `skill_067` (`sweep-objects`).

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Verifier

- [all paths] `clustered(objects=$objects, radius_m=$radius_m)` — GT: object_pose, support_annotation

## Policy paths

- `push_to_centroid` when always: `policy_109($objects, radius_m=$radius_m)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
