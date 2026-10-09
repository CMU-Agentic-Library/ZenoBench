# policy_061 — pick

Annotation-selected right-hand pick dispatcher

## Scope

One low-level controller invocation. Reported effect: `held_by_right_hand(object)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `max_candidates`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_061.execute(...)`
- Legacy alias: `PolicySuite(rig).pick.execute(...)`
- Class: `PickPolicy`
- Availability: `verified`
- Skill Contract paths: contract_025:pick/inside_cabinet_or_fridge, contract_025:pick/annotation_dispatch, contract_059:empty/pick_each_inside, contract_061:restore/dispatch_pick_place
- Legacy family Contracts: contract_002

## Recorded evidence

Annotation-dispatching policy; exercised by verified route-specific policies.
