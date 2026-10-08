# policy_047 — release_articulated_handle

完成关节移动后放开把手

## Scope

One low-level controller invocation. Reported effect: `handle_released`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_047.execute(...)`
- Legacy alias: `PolicySuite(rig).release_articulated_handle.execute(...)`
- Class: `ReleaseArticulatedHandlePolicy`
- Availability: `verified`
- Skill Contract paths: contract_048:open/drawer, contract_048:open/hinged_door
- Referenced as support by legacy families: contract_004, contract_005

## Recorded evidence

Isaac Sim: release_articulated_handle breakfast_fridge, both fingers opened, 2026-10-01
