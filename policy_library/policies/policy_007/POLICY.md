# policy_007 — set_waist_pitch

设置腰部前后俯仰角

## Scope

One low-level controller invocation. Reported effect: `waist_at(pitch_rad)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `pitch_rad`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_007.execute(...)`
- Legacy alias: `PolicySuite(rig).set_waist_pitch.execute(...)`
- Class: `SetWaistPitchPolicy`
- Availability: `verified`
- Skill Contract paths: contract_015:bend/to_pitch
- Legacy family Contracts: contract_008

## Recorded evidence

Isaac Sim: lean_forward/straighten_waist, 2026-10-01
