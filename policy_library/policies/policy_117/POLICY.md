# policy_117 — view_support

Drive to the stand-off pose (within base_near) from which one head camera frame holds the whole support surface, else the one that sees most of it, and aim the head at it.

## Scope

One low-level controller invocation. Reported effect: `in_view(support)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `support`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_117.execute(...)`
- Legacy alias: `PolicySuite(rig).view_support.execute(...)`
- Class: `ViewSupportPolicy`
- Availability: `callable`
- Skill Contract paths: contract_080:mark_spots/view_and_mark

## Recorded evidence

pending Isaac Sim check (visual prompting, 2026-11-15)
