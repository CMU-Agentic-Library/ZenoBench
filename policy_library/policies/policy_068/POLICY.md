# policy_068 — look_at

Aim head yaw/pitch at a target; record visible objects.

## Scope

One low-level controller invocation. Reported effect: `in_view(target), observed(target)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `target`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_068.execute(...)`
- Legacy alias: `PolicySuite(rig).look_at.execute(...)`
- Class: `LookAtPolicy`
- Availability: `callable`
- Skill Contract paths: contract_019:look/head_only, contract_019:look/turn_then_head

## Recorded evidence

pending Isaac Sim check (skill library v2)
