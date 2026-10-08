# policy_081 — roll_cylinder

Roll a lying cylinder by pushing above its axis.

## Scope

One low-level controller invocation. Reported effect: `object_rolled(name)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `distance_m`: positional_or_keyword; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_081.execute(...)`
- Legacy alias: `PolicySuite(rig).roll_cylinder.execute(...)`
- Class: `RollCylinderPolicy`
- Availability: `callable`
- Skill Contract paths: contract_042:roll/push_above_axis

## Recorded evidence

pending Isaac Sim check (skill library v2)
