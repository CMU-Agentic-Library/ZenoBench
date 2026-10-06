# contract_057 — Ready floor reach

Lower and lean toward a floor object, then verify a fresh reachable pregrasp.

Paired SkillNode: `skill_049`. Status: `representative_runs_only`.

## Inputs

- `object`: object_ref

## Preconditions

- `right_hand_empty` — policy_attempt
- `object_on_floor` — policy_attempt
- `pregrasp_reachable` — policy_attempt

## Planner action predicate

`ready_floor_object(object)` — reported only after the measured state facts pass.

## Measured postconditions

- `floor_reach_ready` — contract_runner

## Grounded noun slots

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_042` with ['object']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: custom `floor_reach`.
