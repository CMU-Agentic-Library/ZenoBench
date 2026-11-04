---
name: navigate-place
description: "Drive the holonomic base to a free stand-off pose next to a room, piece of furniture, support, articulated part or object. An empty arm is tucked and hangs at the side (inside the base footprint) while the base drives, then returns to the tuck; a loaded one is held in the compact carry pose."
---

# Navigate to a place (`skill_001`)

`navigate(destination: place_ref)`

Drive the holonomic base to a free stand-off pose next to a room, piece of furniture, support, articulated part or object. An empty arm is tucked and hangs at the side (inside the base footprint) while the base drives, then returns to the tuck; a loaded one is held in the compact carry pose.

## When to use

The robot must be in another room or next to another piece of furniture.

## Not to be confused with

- `retreat`: retreat moves straight back from a place without a destination.

## Inputs

- `destination` (`place_ref`): Where to go: a room, furniture, support, articulated part or object.

## Outputs

- `base_pose` (`pose2d`): Measured base pose [x, y, yaw_deg] at arrival.

## Applicability

Always applicable.

## Preconditions (checked on live GT state before moving)

- none

## Postconditions (verified on live GT state)

- `base_near(place=$destination)` — Base centre within 1.3 m of the place's footprint (inside the room for a room). GT: base_pose, scene_annotation.

## Verifier

after the policy chain, every listed predicate is evaluated on ground-truth simulator state (object poses, joint values, finger gaps, head-camera geometry, thermal state, event log); the node succeeds only if all hold for the selected path:

- `base_near(place=$destination)` (all paths)

## May invalidate

`base_near(*)`, `reachable(*)`, `facing(*)`, `in_view(*)`, `base_clear_of(*)`, `pointing_at(*)`, `presenting(*)`

## Policy paths (first match on the bound nouns)

### `two_hand_carry` — when robot.both_hold_same

1. `policy_097($destination) as plan`
2. `policy_058(@robot.right_object, #plan.pose)`
- An object held by both grippers moves at the slow bimanual carry speed.

### `drive` — when always (default path)

1. `policy_092($destination)`
- The nearest reachable stand-off; a load is carried in the carry pose (raised clear of the destination surface) and the base drives slower.

## Relations

- Previous step: `retreat` (`skill_004`) (then) — the robot must leave after backing out
- Previous step: `stand` (`skill_006`) (then) — the robot drives after low work
- Previous step: `straighten` (`skill_008`) (then) — the robot drives after a bent reach
- Previous step: `tuck` (`skill_009`) (then) — the robot drives next
- Previous step: `reset` (`skill_010`) (then) — after a failed manipulation, before driving on
- Previous step: `search` (`skill_013`) (then) — the found object must be fetched
- Previous step: `pick` (`skill_017`) (then) — the object must be carried elsewhere
- Previous step: `lift` (`skill_023`) (then) — the object is carried over furniture
- Previous step: `close` (`skill_041`) (then) — the robot leaves
- Previous step: `explore_furniture` (`skill_071`) (then) — an object seen on a layer must be fetched
- Next step: `pick` (`skill_017`) (enables) — the object to grasp is the destination
- Next step: `look` (`skill_011`) (then) — the destination must be observed first
- Fallback on failure: `retreat` (`skill_004`) (recover) — navigation fails because the base or load is wedged against furniture
- Fallback on failure: `tuck` (`skill_009`) (recover) — navigation fails because the empty arm cannot fold
- Fallback on failure: `lift` (`skill_023`) (recover) — a carried object hangs too low for the doorway clearance
- Is a fallback for: `look` (`skill_011`) (repair) — the line of sight is blocked
- Is a fallback for: `identify` (`skill_057`) (recover) — the object is not visible from here
- Alternative: `face` (`skill_003`) — use navigate instead when turning in place is blocked by furniture
- Alternative: `sidestep` (`skill_055`) — use navigate instead when a larger move is needed

## Failure

Stop and report the error code and the measured pre- and postconditions. Nothing is retried or repaired automatically.

- no free stand-off pose
- no base path
- carried object slipped (Dropped)

Paired Contract: `contract_009`.
