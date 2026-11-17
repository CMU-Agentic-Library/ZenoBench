# policy_118 — mark_spots

Number up to six spread-out free spots for the held object on the support in the head camera view and draw them on the head image (visual prompting for place hint_xy).

## Scope

One low-level controller invocation. Reported effect: `spots(object, support)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `object`: positional_or_keyword; required
- `support`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_118.execute(...)`
- Legacy alias: `PolicySuite(rig).mark_spots.execute(...)`
- Class: `MarkSpotsPolicy`
- Availability: `callable`
- Skill Contract paths: contract_080:mark_spots/view_and_mark

## Recorded evidence

pending Isaac Sim check (visual prompting, 2026-11-15)
