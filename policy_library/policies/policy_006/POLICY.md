# policy_006 — raise_torso

升躯干到高位或指定高度

## Scope

One low-level controller invocation. Reported effect: `torso_raised`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `height`: positional_or_keyword; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_006.execute(...)`
- Legacy alias: `PolicySuite(rig).raise_torso.execute(...)`
- Class: `RaiseTorsoPolicy`
- Availability: `verified`
- Direct Contract routes: contract_040
- Legacy family Contracts: contract_008

## Recorded evidence

Isaac Sim: raise_torso, 2026-10-01
