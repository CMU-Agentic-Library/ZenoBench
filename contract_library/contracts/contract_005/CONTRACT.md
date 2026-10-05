# contract_005 — close.v1

Close one annotated door or drawer.

## Scope

One measured closure of an annotated door or drawer.

## Inputs

- `articulated`: articulated_id; required

## Requires

- `articulated_annotated` — runner
- `closure_path_clear` — policy_attempt

## Achieves on success

- `joint_closed` — runner

## Routes

- `auto` → `policy_063`
- `handle` → `policy_023`
- `powered` → `policy_025`

Legacy alias: `close.v1`. Runtime binding: `zeno_skills.contracts.CONTRACTS`.
