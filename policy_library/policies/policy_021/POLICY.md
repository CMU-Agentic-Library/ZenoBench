# policy_021 — place_microwave

从正面把物品送入微波炉腔体

## Scope

One low-level controller invocation. Reported effect: `inside(object,cavity)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `support`: positional_or_keyword; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_021.execute(...)`
- Legacy alias: `PolicySuite(rig).place_microwave.execute(...)`
- Class: `MicrowavePlacePolicy`
- Availability: `verified`
- Skill Contract paths: contract_026:place/microwave
- Legacy family Contracts: contract_003

## Recorded evidence

Isaac Sim dedicated appliance fixture: cup picked from cabinet top and physically inserted through open microwave door; measured on inside_floor true, in_cavity true, tilt 0 deg; runs/verify_callable_microwave_cycle_cup, 2026-10-01
