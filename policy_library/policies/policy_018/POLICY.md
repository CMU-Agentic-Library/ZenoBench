# policy_018 — microwave_cavity_insert

持物从微波炉正面送入腔体，不松爪

## Scope

One low-level controller invocation. Reported effect: `held_object_inside_cavity`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `support`: positional_or_keyword; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_018.execute(...)`
- Legacy alias: `PolicySuite(rig).microwave_cavity_insert.execute(...)`
- Class: `MicrowaveCavityInsertPolicy`
- Availability: `verified`
- Direct Contract routes: contract_013, contract_022
- Referenced as support by legacy families: contract_003

## Recorded evidence

Isaac Sim: heat_breakfast fridge -> microwave -> dining table, 100% progress, 2026-10-01; runs/heat_breakfast/result.json
