# contract_043 — Expose a flat object edge

Push a flat object to a measured, graspable support overhang.

Paired SkillNode: `skill_035`. Status: `representative_runs_only`.

## Inputs

- `object`: object_ref

## Preconditions

- `right_hand_empty` — contract_precheck
- `object_on_annotated_support` — policy_attempt
- `free_support_edge` — policy_attempt

## Planner action predicate

`expose_flat_object_edge(object)` — reported only after the measured state facts pass.

## Measured postconditions

- `edge_overhang_ready` — contract_runner

## Grounded noun slots

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_grasp_type': 'edge_pinch_after_push'}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_045` with ['object']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: custom `edge_ready`.
