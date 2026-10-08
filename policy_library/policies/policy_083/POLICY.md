# policy_083 — center_on_support

Push an object back from the support edges.

## Scope

One low-level controller invocation. Reported effect: `away_from_edge(name, margin)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `margin_m`: positional_or_keyword; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_083.execute(...)`
- Legacy alias: `PolicySuite(rig).center_on_support.execute(...)`
- Class: `CenterOnSupportPolicy`
- Availability: `callable`
- Skill Contract paths: contract_041:center/push_inward

## Recorded evidence

pending Isaac Sim check (skill library v2)
