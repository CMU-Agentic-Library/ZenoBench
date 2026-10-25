---
name: explore-room
description: "Cover a room from up to six viewpoints with a left/centre/right head sweep both ways; succeeds when at least 75 % of the room's furniture was seen. A piece of furniture counts once one of its support layers (top or shelf) is in view; seeing every shelf of one piece is explore_furniture."
---

# Explore a room (`skill_014`)

`explore_room(room: room_ref)`

Cover a room from up to six viewpoints with a left/centre/right head sweep both ways; succeeds when at least 75 % of the room's furniture was seen. A piece of furniture counts once one of its support layers (top or shelf) is in view; seeing every shelf of one piece is explore_furniture.

## When to use

A room must be surveyed before planning (unknown layout or objects); one glance per piece of furniture.

## Not to be confused with

- `search`: search looks for one object and stops when found.
- `explore_furniture`: explore_furniture sees every layer of one piece; explore_room counts a piece once one layer is seen.

## Inputs

- `room` (`room_ref`): The room to cover.

## Outputs

- `seen` (`object_list`): Objects observed during the sweep.

## Applicability

Always applicable.

## Preconditions (checked on live GT state before moving)

- none

## Postconditions (verified on live GT state)

- `room_explored(room=$room)` — At least 75 % of the room's furniture was seen (one of its support layers in the head camera). GT: robot_memory, room_annotation.

## Verifier

after the policy chain, every listed predicate is evaluated on ground-truth simulator state (object poses, joint values, finger gaps, head-camera geometry, thermal state, event log); the node succeeds only if all hold for the selected path:

- `room_explored(room=$room)` (all paths)

## May invalidate

`base_near(*)`, `reachable(*)`, `facing(*)`, `in_view(*)`

## Policy paths (first match on the bound nouns)

### `viewpoints` — when always (default path)

1. `policy_069($room)`

## Relations

- Next step: `search` (`skill_013`) (then) — a specific object must then be located
- Next step: `explore_furniture` (`skill_071`) (then) — every shelf of one piece of furniture must be seen
- Is a fallback for: `search` (`skill_013`) (recover) — the object is not on any visited support
- Is a fallback for: `count` (`skill_059`) (recover) — objects of the category may be out of view

## Failure

Stop and report the error code and the measured pre- and postconditions. Nothing is retried or repaired automatically.


Paired Contract: `contract_022`.
