# policy_005 — lower_torso

降躯干到低位或指定高度

## Scope

One low-level controller invocation. Reported effect: `torso_lowered`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `height`: positional_or_keyword; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_005.execute(...)`
- Legacy alias: `PolicySuite(rig).lower_torso.execute(...)`
- Class: `LowerTorsoPolicy`
- Availability: `verified`
- Direct Contract routes: contract_039
- Legacy family Contracts: contract_008

## Recorded evidence

Isaac Sim: lower_torso, 2026-10-01
