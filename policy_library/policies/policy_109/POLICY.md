# policy_109 — sweep_together

Push objects toward their centroid.

## Scope

One low-level controller invocation. Reported effect: `clustered(names)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `names`: positional_or_keyword; required
- `radius_m`: keyword_only; optional
- `rounds`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_109.execute(...)`
- Legacy alias: `PolicySuite(rig).sweep_together.execute(...)`
- Class: `SweepTogetherPolicy`
- Availability: `callable`
- Skill Contract paths: contract_075:sweep/push_to_centroid

## Recorded evidence

pending Isaac Sim check (skill library v2)
