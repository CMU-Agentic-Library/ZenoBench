# policy_077 — left_steady

Pinch a resting container with the left gripper.

## Scope

One low-level controller invocation. Reported effect: `steadied(name)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_077.execute(...)`
- Legacy alias: `PolicySuite(rig).left_steady.execute(...)`
- Class: `LeftSteadyPolicy`
- Availability: `callable`
- Skill Contract paths: contract_035:brace/left_rim_pinch

## Recorded evidence

pending Isaac Sim check (skill library v2)
