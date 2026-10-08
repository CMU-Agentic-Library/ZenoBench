# policy_069 — explore_room

Visit viewpoints in a room and sweep the head.

## Scope

One low-level controller invocation. Reported effect: `room_explored(room)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `room`: positional_or_keyword; required
- `max_views`: keyword_only; optional
- `min_spacing`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_069.execute(...)`
- Legacy alias: `PolicySuite(rig).explore_room.execute(...)`
- Class: `ExploreRoomPolicy`
- Availability: `callable`
- Skill Contract paths: contract_022:explore/viewpoints

## Recorded evidence

pending Isaac Sim check (skill library v2)
