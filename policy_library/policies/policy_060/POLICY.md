# policy_060 — open_door_while_left_holds

左手持物同时用右手开门

## Scope

One low-level controller invocation. Reported effect: `left_holds(object) and door_open`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `object_name`: positional_or_keyword; required
- `door_name`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_060.execute(...)`
- Legacy alias: `PolicySuite(rig).open_door_while_left_holds.execute(...)`
- Class: `OpenDoorWhileLeftHoldsPolicy`
- Availability: `callable`
- Skill Contract paths: contract_048:open/left_holds_load
- Legacy family Contracts: contract_004

## Caveat

依赖稳定左手持物；handover 尚未通过，未建立可验证的左手持物开门前置状态。
