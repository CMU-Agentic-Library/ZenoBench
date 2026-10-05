# contract_004 — open.v1

Move one annotated door or drawer to a measured open joint value.

## Scope

One measured joint opening of an annotated door or drawer; object access is a separate predicate.

## Inputs

- `articulated`: articulated_id; required
- `required_access_to`: object_id; optional

## Requires

- `articulated_annotated` — runner
- `opening_route_feasible` — policy_attempt

## Achieves on success

- `joint_open_enough` — runner

## Routes

- `auto` → `policy_062`
- `handle` → `policy_022`
- `powered` → `policy_024`
- `revolute` → `policy_049`
- `prismatic` → `policy_050`
- `while_left_holds` → `policy_060`

## Outside this contract

- accessible(required_access_to)

Legacy alias: `open.v1`. Runtime binding: `zeno_skills.contracts.CONTRACTS`.
