# policy_019 — microwave_cavity_release

送入腔体后张开夹爪并测量手指位置

## Scope

One low-level controller invocation. Reported effect: `object_released_in_cavity`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_019.execute(...)`
- Legacy alias: `PolicySuite(rig).microwave_cavity_release.execute(...)`
- Class: `MicrowaveCavityReleasePolicy`
- Availability: `verified`
- Direct Contract routes: contract_013, contract_022
- Referenced as support by legacy families: contract_003

## Recorded evidence

Isaac Sim: heat_breakfast fridge -> microwave -> dining table, 100% progress, 2026-10-01; runs/heat_breakfast/result.json
