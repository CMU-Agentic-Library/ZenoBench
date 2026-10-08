# policy_066 — face_target

Rotate the base in place toward a target.

## Scope

One low-level controller invocation. Reported effect: `facing(target)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `target`: positional_or_keyword; required
- `tolerance_deg`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_066.execute(...)`
- Legacy alias: `PolicySuite(rig).face_target.execute(...)`
- Class: `FaceTargetPolicy`
- Availability: `callable`
- Skill Contract paths: contract_011:face/rotate_loaded, contract_019:look/turn_then_head

## Recorded evidence

pending Isaac Sim check (skill library v2)
