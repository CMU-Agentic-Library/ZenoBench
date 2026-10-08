# policy_096 — release_in_place

Open one gripper where the object rests.

## Scope

One low-level controller invocation. Reported effect: `hand_empty(hand)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `hand`: positional_or_keyword; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_096.execute(...)`
- Legacy alias: `PolicySuite(rig).release_in_place.execute(...)`
- Class: `ReleaseInPlacePolicy`
- Availability: `callable`
- Skill Contract paths: contract_029:release/open_in_place

## Recorded evidence

pending Isaac Sim check (skill library v2)
