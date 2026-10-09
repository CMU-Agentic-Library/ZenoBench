# contract_060 — Arrange objects together

Place the listed objects on one support so that they are pairwise within a distance (a place setting).

Verb: `arrange`.

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Verifier

- [all paths] `grouped(objects=$objects, support=$support, max_dist_m=$max_dist_m)` — GT: object_pose, support_annotation

## Policy paths

- `place_near_common_spot` when always: `for each item in $objects: [navigate](destination=$item) -> [pick](object=$item) -> [navigate](destination=$support) -> [place](object=$item, receptacle=$support, hint_xy=@support.roomiest_xy)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
