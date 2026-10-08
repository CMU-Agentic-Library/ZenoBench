# policy_074 — stack_on

Place a held object on another object's top face.

## Scope

One low-level controller invocation. Reported effect: `on_top_of(name, base)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `base`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_074.execute(...)`
- Legacy alias: `PolicySuite(rig).stack_on.execute(...)`
- Class: `StackOnPolicy`
- Availability: `callable`
- Skill Contract paths: contract_028:stack/top_face

## Recorded evidence

pending Isaac Sim check (skill library v2)
