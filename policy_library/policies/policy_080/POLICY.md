# policy_080 — separate_from_neighbour

Push an object away from its nearest neighbour.

## Scope

One low-level controller invocation. Reported effect: `grasp_clearance(name)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `target_gap`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_080.execute(...)`
- Legacy alias: `PolicySuite(rig).separate_from_neighbour.execute(...)`
- Class: `SeparateFromNeighbourPolicy`
- Availability: `callable`
- Skill Contract paths: contract_040:separate/push_apart

## Recorded evidence

pending Isaac Sim check (skill library v2)
