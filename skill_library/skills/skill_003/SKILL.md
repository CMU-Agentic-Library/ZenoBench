---
name: face-target
description: "Rotate the base in place until it faces the target (heading error <= 20 deg)."
---

# Face a target (`skill_003`)

`face(target: entity_ref)`

Rotate the base in place until it faces the target (heading error <= 20 deg).

## When to use

The target is beside or behind the robot and only the heading must change.

## Not to be confused with

- `look`: look aims the head camera and turns the base only when the target is beyond the head's range; face always turns the base.

## Inputs

- `target` (`entity_ref`): What to face.

## Outputs

- `base_yaw_deg` (`number`): Measured heading after the turn.

## Applicability

Always applicable.

## Preconditions (checked on live GT state before moving)

- none

## Postconditions (verified on live GT state)

- `facing(target=$target)` — Base heading within 20 deg of the target bearing. GT: base_pose, scene_annotation.

## Verifier

after the policy chain, every listed predicate is evaluated on ground-truth simulator state (object poses, joint values, finger gaps, head-camera geometry, thermal state, event log); the node succeeds only if all hold for the selected path:

- `facing(target=$target)` (all paths)

## May invalidate

`reachable(*)`, `in_view(*)`, `pointing_at(*)`

## Policy paths (first match on the bound nouns)

### `already_facing` — when target.bearing_abs_deg <= 2

- The heading error is already under 2 deg: nothing moves.

### `rotate` — when always (default path)

1. `policy_066($target)`
- An empty arm is tucked first (which also raises the torso and straightens the waist); the turn is checked over the whole robot and a load turns slower.

## Relations

- Next step: `look` (`skill_011`) (then) — the target must be observed
- Next step: `point` (`skill_015`) (then) — the target must be indicated
- Alternative: `navigate` (`skill_001`) — turning in place is blocked by furniture

## Failure

Stop and report the error code and the measured pre- and postconditions. Nothing is retried or repaired automatically.

- turning in place would hit furniture

Paired Contract: `contract_011`.
