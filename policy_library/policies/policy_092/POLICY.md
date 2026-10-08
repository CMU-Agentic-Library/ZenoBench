# policy_092 — navigate_to_place

Drive to a free stand-off pose near a room/furniture/support/object.

## Scope

One low-level controller invocation. Reported effect: `base_near(place)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `place`: positional_or_keyword; required
- `max_tries`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_092.execute(...)`
- Legacy alias: `PolicySuite(rig).navigate_to_place.execute(...)`
- Class: `NavigateToPlacePolicy`
- Availability: `callable`
- Skill Contract paths: contract_059:empty/pick_each_inside, contract_061:restore/dispatch_pick_place

## Recorded evidence

pending Isaac Sim check (skill library v2)
