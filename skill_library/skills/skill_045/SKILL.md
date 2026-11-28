---
name: cover-container
description: "Lay the held lid centred on the container rim (within 3 cm, tilt <= 12 deg) and release it."
---

# Cover a container with a lid (`skill_045`)

`cover(container: container_ref, lid: lid_ref)`

Lay the held lid centred on the container rim (within 3 cm, tilt <= 12 deg) and release it.

## When to use

A container must be closed with its lid.

## Not to be confused with

- `uncover`: opposite direction.
- `place`: cover rests the lid on the rim.

## Inputs

- `container` (`container_ref`): The pot or box to cover.
- `lid` (`lid_ref`): The held lid: an object tagged lid (a pot lid, or a plate set on the rim).

## Applicability

Requires holding(hand=any, object=$lid); base_near(place=$container); uncovered(container=$container).

## Preconditions (checked on live GT state before moving)

- `holding(hand=any, object=$lid)` — The object is in the given gripper (any: in either): TCP-to-body distance unchanged since the grasp, and the fingers not shut unless it has kept within 3 cm (a thin rim pinched). GT: gripper_state, finger_joints, object_pose, arm_fk.
- `base_near(place=$container)` — Base centre within 1.3 m of the place's footprint (inside the room for a room). GT: base_pose, scene_annotation.
- `uncovered(container=$container)` — No lid rests on the container rim. GT: object_pose, container_profile, asset_tags.

## Postconditions (verified on live GT state)

- `covered(container=$container, lid=$lid)` — The lid rests centred on the container rim (3 cm xy, 3 cm height, 12 deg tilt). GT: object_pose, container_profile.
- `not holding(hand=any, object=$lid)` — Must be false: The object is in the given gripper (any: in either): TCP-to-body distance unchanged since the grasp, and the fingers not shut unless it has kept within 3 cm (a thin rim pinched). GT: gripper_state, finger_joints, object_pose, arm_fk.

## Verifier

after the policy chain, every listed predicate is evaluated on ground-truth simulator state (object poses, joint values, finger gaps, head-camera geometry, thermal state, event log); the node succeeds only if all hold for the selected path:

- `covered(container=$container, lid=$lid)` (all paths)
- `not holding(hand=any, object=$lid)` (all paths)

## May invalidate

`uncovered($container)`, `holding(*,$lid)`

## Policy paths (first match on the bound nouns)

### `rim_plane` — when lid.is_lid

1. `policy_087($lid, $container)`

## Relations

- Previous step: `stir` (`skill_038`) (enables) — the pot is covered again
- Next step: `heat` (`skill_043`) (then) — the pot is heated with its lid on (heat itself needs no lid)
- Alternative: `uncover` (`skill_046`) — opposite effect

## Failure

Stop and report the error code and the measured pre- and postconditions. Nothing is retried or repaired automatically.


Paired Contract: `contract_053`.
