# policy_071 — point_at

Point closed right fingers at a target.

## Scope

One low-level controller invocation. Reported effect: `pointing_at(target)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `target`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_071.execute(...)`
- Legacy alias: `PolicySuite(rig).point_at.execute(...)`
- Class: `PointAtPolicy`
- Availability: `callable`
- Skill Contract paths: contract_023:point/turn_and_point

## Recorded evidence

pending Isaac Sim check (skill library v2)
