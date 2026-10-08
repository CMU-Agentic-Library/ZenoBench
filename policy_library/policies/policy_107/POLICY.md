# policy_107 — touch_object

Bring closed fingertips onto an object's top and back off.

## Scope

One low-level controller invocation. Reported effect: `touched(name)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_107.execute(...)`
- Legacy alias: `PolicySuite(rig).touch_object.execute(...)`
- Class: `TouchObjectPolicy`
- Availability: `callable`
- Skill Contract paths: contract_073:touch/fingertip_top

## Recorded evidence

pending Isaac Sim check (skill library v2)
