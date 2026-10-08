# policy_113 — dip_utensil

Lower a held spoon tip into a container and lift it out.

## Scope

One low-level controller invocation. Reported effect: `dipped(container)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `tool`: positional_or_keyword; required
- `container`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_113.execute(...)`
- Legacy alias: `PolicySuite(rig).dip_utensil.execute(...)`
- Class: `DipUtensilPolicy`
- Availability: `callable`
- Skill Contract paths: contract_077:dip/tip_below_rim

## Recorded evidence

pending Isaac Sim check (skill library v2)
