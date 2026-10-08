# policy_104 — wave_hand

Raise the empty right hand and swing it.

## Scope

One low-level controller invocation. Reported effect: `waved()`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `swings`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_104.execute(...)`
- Legacy alias: `PolicySuite(rig).wave_hand.execute(...)`
- Class: `WaveHandPolicy`
- Availability: `callable`
- Skill Contract paths: contract_068:wave/raised_swing

## Recorded evidence

pending Isaac Sim check (skill library v2)
