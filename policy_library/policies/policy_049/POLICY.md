# policy_049 — open_revolute_door

只选择旋转铰链门的把手轨迹

## Scope

One low-level controller invocation. Reported effect: `joint_at(open_q)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_049.execute(...)`
- Legacy alias: `PolicySuite(rig).open_revolute_door.execute(...)`
- Class: `OpenRevoluteDoorPolicy`
- Availability: `verified`
- Direct Contract routes: contract_011, contract_055
- Legacy family Contracts: contract_004

## Recorded evidence

Isaac Sim: open_revolute_door breakfast_fridge, joint reached -0.527 rad for -0.611 rad goal, 2026-10-01 Active Contract hinged-door pass: runs/check_50_manual, 2026-10-06.
