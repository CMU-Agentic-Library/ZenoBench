---
name: explore-furniture
description: "See every support layer of one piece of furniture (each shelf, the top, a cabinet's inside shelves): sweep from where the robot stands when it is already near, else from up to three stand-off poses in front of it, aiming the head at each layer not seen yet, then again with the torso lowered for the layers still hidden (a bottom shelf behind the front edge of the shelf above). A layer is seen when the space just above its board is in the head camera and no board of the piece is in the way. Succeeds only when every layer was seen; a closed cabinet door hides its inside layers."
---

# Explore a piece of furniture (`skill_071`)

`explore_furniture(furniture: furniture_ref)`

See every support layer of one piece of furniture (each shelf, the top, a cabinet's inside shelves): sweep from where the robot stands when it is already near, else from up to three stand-off poses in front of it, aiming the head at each layer not seen yet, then again with the torso lowered for the layers still hidden (a bottom shelf behind the front edge of the shelf above). A layer is seen when the space just above its board is in the head camera and no board of the piece is in the way. Succeeds only when every layer was seen; a closed cabinet door hides its inside layers.

## When to use

Every shelf of one bookcase, shelf unit or cabinet must be seen: what is on each layer, or which layer is free.

## Not to be confused with

- `explore_room`: explore_room glances at every piece of a room, one layer each.
- `look`: look aims at one target; explore_furniture at every layer of one piece.

## Inputs

- `furniture` (`furniture_ref`): The bookcase, shelf unit, table, desk or cabinet to cover.

## Outputs

- `seen` (`object_list`): Objects observed during the sweep.

## Applicability

Always applicable.

## Preconditions (checked on live GT state before moving)

- none

## Postconditions (verified on live GT state)

- `furniture_explored(furniture=$furniture)` — Every support layer of the furniture (each shelf, the top) was seen in the head camera. GT: robot_memory, support_annotation.

## Verifier

after the policy chain, every listed predicate is evaluated on ground-truth simulator state (object poses, joint values, finger gaps, head-camera geometry, thermal state, event log); the node succeeds only if all hold for the selected path:

- `furniture_explored(furniture=$furniture)` (all paths)

## May invalidate

`base_near(*)`, `reachable(*)`, `facing(*)`, `in_view(*)`

## Policy paths (first match on the bound nouns)

### `layers` — when always (default path)

1. `policy_116($furniture)`

## Relations

- Previous step: `explore_room` (`skill_014`) (then) — every shelf of one piece of furniture must be seen
- Next step: `navigate` (`skill_001`) (then) — an object seen on a layer must be fetched
- Fallback on failure: `open` (`skill_040`) (recover) — a closed cabinet door hides the inside layers
- Is a fallback for: `search` (`skill_013`) (recover) — the object may sit on a shelf the sweep only glanced at
- Alternative: `look` (`skill_011`) — only one layer must be seen

## Failure

Stop and report the error code and the measured pre- and postconditions. Nothing is retried or repaired automatically.

- a layer stays hidden from every stand-off pose, standing and crouched
- a closed door hides a cabinet's inside layers
- holding an object: the torso is not lowered, so low shelves may stay hidden

Paired Contract: `contract_079`.
