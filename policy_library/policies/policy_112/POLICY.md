# policy_112 — count_category

Sweep the head and count visible objects of a category.

## Scope

One low-level controller invocation. Reported effect: `counted(category)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `category`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_112.execute(...)`
- Legacy alias: `PolicySuite(rig).count_category.execute(...)`
- Class: `CountCategoryPolicy`
- Availability: `callable`
- Skill Contract paths: contract_067:count/head_sweep

## Recorded evidence

pending Isaac Sim check (skill library v2)
