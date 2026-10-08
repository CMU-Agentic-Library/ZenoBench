# policy_075 — rotate_held

Turn a held object about the vertical axis.

## Scope

One low-level controller invocation. Reported effect: `yaw_rotated(name, degrees)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `degrees`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_075.execute(...)`
- Legacy alias: `PolicySuite(rig).rotate_held.execute(...)`
- Class: `RotateHeldPolicy`
- Availability: `callable`
- Skill Contract paths: contract_033:rotate/wrist_yaw, contract_072:square/pick_rotate_place

## Recorded evidence

pending Isaac Sim check (skill library v2)
