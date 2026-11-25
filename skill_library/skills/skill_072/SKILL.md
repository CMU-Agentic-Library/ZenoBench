---
name: mark-spots-support
description: "Show where the held object can go on a support surface: see the surface clearly from one or two stand-off poses (one where the robot stands when it does about as well; a long table: one view per half), standing up with the head aimed at it, and number up to sixteen free spots on those head images, one set of numbers over all of them: one for each set of objects on the surface a spot can be within 15 cm of (by one object, between two, by none, ...). Every spot fits the object at any turn with room left to its neighbours and is in view. The numbered images come with the next observation (one images entry per view, overlay \"place_spots\" and view k); disc n is spots[n-1] on every image it is drawn on. Nothing is placed: place the object with place(object, receptacle=support, hint_xy=<the chosen spot's xy>)."
---

# Mark free spots on a support (`skill_072`)

`mark_spots(object: object_ref, support: support_ref)`

Show where the held object can go on a support surface: see the surface clearly from one or two stand-off poses (one where the robot stands when it does about as well; a long table: one view per half), standing up with the head aimed at it, and number up to sixteen free spots on those head images, one set of numbers over all of them: one for each set of objects on the surface a spot can be within 15 cm of (by one object, between two, by none, ...). Every spot fits the object at any turn with room left to its neighbours and is in view. The numbered images come with the next observation (one images entry per view, overlay "place_spots" and view k); disc n is spots[n-1] on every image it is drawn on. Nothing is placed: place the object with place(object, receptacle=support, hint_xy=<the chosen spot's xy>).

## When to use

A held object must go on a large surface and where on it matters (next to something, away from something, a free corner): choose a numbered spot on the image instead of guessing coordinates.

## Not to be confused with

- `place`: place puts the object down; mark_spots only shows where it could go.
- `look`: look aims the camera at a target; mark_spots frames a whole surface and numbers free spots on it.

## Inputs

- `object` (`object_ref`): The held object (either hand) the spots are for (its footprint).
- `support` (`support_ref`): The table, desk, counter or shelf surface to mark.

## Outputs

- `spots` (`xy_list`): Free spots [x, y] in metres; spot n is the disc numbered n on the image.
- `coverage` (`number`): Fraction of the surface seen clearly in the views (1 = all of it).

## Applicability

Requires holding(hand=any, object=$object).

## Preconditions (checked on live GT state before moving)

- `holding(hand=any, object=$object)` — The object is in the given gripper (any: in either): fingers not shut, TCP-to-body distance unchanged since the grasp. GT: gripper_state, finger_joints, object_pose, arm_fk.

## Postconditions (verified on live GT state)

- `in_view(target=$support)` — Target point inside the head camera frustum, within 5 m, line of sight not blocked by furniture boxes. GT: base_pose, head_joints, head_fk, collision_model.

## Verifier

after the policy chain, every listed predicate is evaluated on ground-truth simulator state (object poses, joint values, finger gaps, head-camera geometry, thermal state, event log); the node succeeds only if all hold for the selected path:

- `in_view(target=$support)` (all paths)

## May invalidate

`base_near(*)`, `reachable(*)`, `facing(*)`, `in_view(*)`

## Policy paths (first match on the bound nouns)

### `view_and_mark` — when always (default path)

1. `policy_117($support)`
2. `policy_118($object, $support)`

## Relations

- Next step: `place` (`skill_018`) (then) — the object goes to the chosen spot
- Alternative: `look` (`skill_011`) — the surface only has to be seen, not marked

## Failure

Stop and report the error code and the measured pre- and postconditions. Nothing is retried or repaired automatically.

- no stand-off pose within reach sees the whole surface: the spots cover the part in view (coverage < 1)
- no free spot for the object is in view
- a spot may be drawn over the arm or the held object (the robot's own body is not checked)

Paired Contract: `contract_080`.
