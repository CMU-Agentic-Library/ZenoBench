# contract_008 — set_posture.v1

Set measured right-arm, torso or waist posture.

## Scope

One measured right-arm, torso, or waist posture adjustment.

## Inputs

- `component`: enum; required
- `target`: number; optional

## Requires

- `right_hand_empty` — policy_attempt
- `target_within_joint_limits` — policy_attempt
- `collision_free_motion` — policy_attempt

## Achieves on success

- `posture_at_target` — runner

## Routes

- `tuck` → `policy_003`
- `torso` → `policy_004`
- `lower` → `policy_005`
- `raise` → `policy_006`
- `waist` → `policy_007`
- `lean` → `policy_008`
- `straighten` → `policy_009`

## Outside this contract

- a task target became reachable solely because posture changed

Legacy alias: `set_posture.v1`. Runtime binding: `zeno_skills.contracts.CONTRACTS`.
