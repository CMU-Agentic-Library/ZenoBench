# policy_004 — set_torso_height

设置躯干升降关节位置

## Scope

One low-level controller invocation. Reported effect: `torso_at(height_m)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `height`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_004.execute(...)`
- Legacy alias: `PolicySuite(rig).set_torso_height.execute(...)`
- Class: `SetTorsoHeightPolicy`
- Availability: `verified`
- Skill Contract paths: contract_013:crouch/to_height
- Legacy family Contracts: contract_008

## Recorded evidence

Isaac Sim: lower_torso/raise_torso, 2026-10-01
