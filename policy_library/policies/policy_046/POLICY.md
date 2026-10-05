# policy_046 — grasp_articulated_handle

抓住门或抽屉把手

## Scope

One low-level controller invocation. Reported effect: `handle_held`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_046.execute(...)`
- Legacy alias: `PolicySuite(rig).grasp_articulated_handle.execute(...)`
- Class: `GraspArticulatedHandlePolicy`
- Availability: `verified`
- Referenced as support by legacy families: contract_004, contract_005

## Recorded evidence

Isaac Sim: grasp_articulated_handle breakfast_fridge, both fingers contacted, 2026-10-01
