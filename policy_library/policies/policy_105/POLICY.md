# policy_105 — nod_head

Pitch the head down and up.

## Scope

One low-level controller invocation. Reported effect: `nodded()`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `times`: keyword_only; optional
- `depth`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_105.execute(...)`
- Legacy alias: `PolicySuite(rig).nod_head.execute(...)`
- Class: `NodHeadPolicy`
- Availability: `callable`
- Skill Contract paths: contract_069:nod/pitch_cycles

## Recorded evidence

pending Isaac Sim check (skill library v2)
