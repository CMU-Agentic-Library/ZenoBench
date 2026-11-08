---
name: bend-waist
description: "Pitch the waist forward to extend the reach over a deep surface. A held object pitches forward with the body by the same angle."
---

# Bend the waist (`skill_007`)

`bend(pitch_rad: positive_number?)`

Pitch the waist forward to extend the reach over a deep surface. A held object pitches forward with the body by the same angle.

## When to use

A target is just beyond arm reach over a counter and leaning forward helps.

## Not to be confused with

- `crouch`: crouch lowers the torso; bend tilts the waist.

## Inputs

- `pitch_rad` (`positive_number`, optional): Forward pitch in rad, 0.1 to 0.69; omit for the maximum.

## Applicability

Always applicable.

## Preconditions (checked on live GT state before moving)

- none

## Postconditions (verified on live GT state)

- `not waist_straight()` — Must be false: Waist pitch within 0.05 rad of upright. GT: waist_joint.

## Verifier

after the policy chain, every listed predicate is evaluated on ground-truth simulator state (object poses, joint values, finger gaps, head-camera geometry, thermal state, event log); the node succeeds only if all hold for the selected path:

- `not waist_straight()` (all paths)
- `waist_bent(min_pitch_rad=$pitch_rad)` (path to_pitch)
- `waist_bent(min_pitch_rad=0.6)` (path full)

## May invalidate

`waist_straight()`, `reachable(*)`, `in_view(*)`

## Policy paths (first match on the bound nouns)

### `to_pitch` — when args.pitch_rad is given

1. `policy_007($pitch_rad)`
- extra postcondition `waist_bent(min_pitch_rad=$pitch_rad)`

### `full` — when always (default path)

1. `policy_008()`
- extra postcondition `waist_bent(min_pitch_rad=0.6)`

## Relations

- Next step: `straighten` (`skill_008`) (then) — the reach is done
- Next step: `pick` (`skill_017`) (then) — the object lies deep on the surface
- Alternative: `crouch` (`skill_005`) — the target is low rather than far away

## Failure

Stop and report the error code and the measured pre- and postconditions. Nothing is retried or repaired automatically.


Paired Contract: `contract_015`.
