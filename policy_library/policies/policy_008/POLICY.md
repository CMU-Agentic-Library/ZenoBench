# policy_008 — lean_forward

腰部前俯到指定角度

## Scope

One low-level controller invocation. Reported effect: `waist_leaned`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `pitch_rad`: positional_or_keyword; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_008.execute(...)`
- Legacy alias: `PolicySuite(rig).lean_forward.execute(...)`
- Class: `LeanForwardPolicy`
- Availability: `verified`
- Skill Contract paths: contract_015:bend/full
- Legacy family Contracts: contract_008

## Recorded evidence

Isaac Sim: lean_forward, 2026-10-01
