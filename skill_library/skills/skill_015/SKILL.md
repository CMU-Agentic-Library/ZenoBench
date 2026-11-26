---
name: point-target
description: "Point the closed fingers at a target (finger axis within 8 deg) to indicate it."
---

# Point at a target (`skill_015`)

`point(target: entity_ref)`

Point the closed fingers at a target (finger axis within 8 deg) to indicate it.

## When to use

A person must be shown an object or place without touching it.

## Not to be confused with

- `touch`: point does not make contact.

## Inputs

- `target` (`entity_ref`): What to indicate.

## Applicability

Requires hand_empty(hand=any).

## Preconditions (checked on live GT state before moving)

- `hand_empty(hand=any)` — The given gripper holds nothing (any: at least one does not; both: neither does). GT: gripper_state.

## Postconditions (verified on live GT state)

- `pointing_at(target=$target)` — Either hand's finger axis points at the target within 8 deg. GT: arm_fk, scene_annotation.
- `hand_empty(hand=any)` — The given gripper holds nothing (any: at least one does not; both: neither does). GT: gripper_state.

## Verifier

after the policy chain, every listed predicate is evaluated on ground-truth simulator state (object poses, joint values, finger gaps, head-camera geometry, thermal state, event log); the node succeeds only if all hold for the selected path:

- `pointing_at(target=$target)` (all paths)
- `hand_empty(hand=any)` (all paths)

## May invalidate

`arm_stowed(*)`, `reachable(*)`

## Policy paths (first match on the bound nouns)

### `front` — when target.bearing_abs_deg <= 60

1. `policy_071($target)`
- The point skill on the motion layers (HAND_PLAN 9h); the old chain of primitives (close, aim, right_tcp_move) is gone.

### `turn_and_point` — when always (default path)

1. `policy_071($target)`

## Relations

- Previous step: `face` (`skill_003`) (then) — the target must be indicated
- Previous step: `wave` (`skill_060`) (enables) — the robot then indicates something
- Next step: `tuck` (`skill_009`) (then) — the gesture is finished
- Alternative: `look` (`skill_011`) — a gaze is enough to indicate the target
- Alternative: `touch` (`skill_065`) — use point instead when contact is not allowed

## Failure

Stop and report the error code and the measured pre- and postconditions. Nothing is retried or repaired automatically.


Paired Contract: `contract_023`.
