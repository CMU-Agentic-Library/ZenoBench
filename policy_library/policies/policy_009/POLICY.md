# policy_009 — straighten_waist

腰部返回中立姿态

## Scope

One low-level controller invocation. Reported effect: `waist_neutral`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- None.

## Binding and status

- Runtime: `PolicySuite(rig).policy_009.execute(...)`
- Legacy alias: `PolicySuite(rig).straighten_waist.execute(...)`
- Class: `StraightenWaistPolicy`
- Availability: `verified`
- Skill Contract paths: contract_016:straighten/upright
- Legacy family Contracts: contract_008

## Recorded evidence

Isaac Sim: straighten_waist, 2026-10-01
