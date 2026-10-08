# policy_091 — left_arm_fold

Fold the empty left arm.

## Scope

One low-level controller invocation. Reported effect: `arm_stowed(left)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- None.

## Binding and status

- Runtime: `PolicySuite(rig).policy_091.execute(...)`
- Legacy alias: `PolicySuite(rig).left_arm_fold.execute(...)`
- Class: `LeftArmFoldPolicy`
- Availability: `callable`
- Skill Contract paths: contract_017:tuck/left

## Recorded evidence

pending Isaac Sim check (skill library v2)
