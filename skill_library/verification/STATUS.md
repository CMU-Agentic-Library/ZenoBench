# SkillNode physical verification status

All 50 SkillNode/Contract definitions pass the static pairing and schema checks. A physical pass means at least one Contract invocation finished with its measured postconditions true in Isaac Sim; it does not guarantee success for every noun or scene.

| SkillNode | Contract | Status | Successful path(s) | Evidence |
| --- | --- | --- | --- | --- |
| `skill_001` | `contract_009` | physical pass | `fixed` | [check_42_toy_carry](../../runs/check_42_toy_carry/result.json) |
| `skill_002` | `contract_010` | physical pass | `fixed` | [check_42_toy_carry](../../runs/check_42_toy_carry/result.json) |
| `skill_003` | `contract_011` | physical pass | `manual_drawer`, `powered_microwave` | [check_42_manual_doors](../../runs/check_42_manual_doors/result.json), [check_42_powered_doors](../../runs/check_42_powered_doors/result.json) |
| `skill_004` | `contract_012` | physical pass | `fixed`, `top_pinch` | [node_contract_one_fruit](../../runs/node_contract_one_fruit/result.json), [node_contract_near_apple](../../runs/node_contract_near_apple/result.json) |
| `skill_005` | `contract_013` | physical pass | `microwave_support` | [noun_path_microwave](../../runs/noun_path_microwave/result.json) |
| `skill_006` | `contract_014` | physical pass | `fixed` | [node_contract_one_fruit](../../runs/node_contract_one_fruit/result.json), [noun_path_one_fruit](../../runs/noun_path_one_fruit/result.json) |
| `skill_007` | `contract_015` | physical pass | `manual_handle`, `powered_microwave` | [check_42_manual_doors](../../runs/check_42_manual_doors/result.json), [check_42_powered_doors](../../runs/check_42_powered_doors/result.json) |
| `skill_008` | `contract_016` | physical pass | `fixed` | [check_42_push](../../runs/check_42_push/result.json) |
| `skill_009` | `contract_017` | physical pass | `fixed` | [check_42_powered_doors](../../runs/check_42_powered_doors/result.json) |
| `skill_010` | `contract_018` | physical pass | `fixed` | [node_contract_heat_wait](../../runs/node_contract_heat_wait/result.json) |
| `skill_011` | `contract_019` | physical pass | `fixed` | [check_42_posture](../../runs/check_42_posture/result.json), [check_42_posture_corrected](../../runs/check_42_posture_corrected/result.json) |
| `skill_012` | `contract_020` | physical pass | `fixed` | [check_42_posture_corrected](../../runs/check_42_posture_corrected/result.json) |
| `skill_013` | `contract_021` | physical pass | `fixed` | [check_42_posture_corrected](../../runs/check_42_posture_corrected/result.json) |
| `skill_014` | `contract_022` | physical pass | `fixed` | [node_contract_microwave_place](../../runs/node_contract_microwave_place/result.json), [check_42_cavity_round](../../runs/check_42_cavity_round/result.json) |
| `skill_015` | `contract_023` | attempted; no pass | — | [check_50_cavity_legacy_prep](../../runs/check_50_cavity_legacy_prep/result.json) |
| `skill_016` | `contract_024` | physical pass | `fixed` | [check_42_flat_edge](../../runs/check_42_flat_edge/result.json) |
| `skill_017` | `contract_025` | physical pass | `fixed` | [check_42_handle_pick](../../runs/check_42_handle_pick/result.json) |
| `skill_018` | `contract_026` | physical pass | `fixed` | [check_42_moving_pick_near](../../runs/check_42_moving_pick_near/result.json) |
| `skill_019` | `contract_027` | physical pass | `fixed` | [check_42_moving_place](../../runs/check_42_moving_place/result.json) |
| `skill_020` | `contract_028` | attempted; no pass | — | [check_42_floor_corner_toycar](../../runs/check_42_floor_corner_toycar/result.json) |
| `skill_021` | `contract_029` | blocked by preparation | — | [check_42_bimanual_carry](../../runs/check_42_bimanual_carry/result.json) |
| `skill_022` | `contract_030` | blocked by preparation | — | [check_42_left_hold_door](../../runs/check_42_left_hold_door/result.json) |
| `skill_023` | `contract_031` | physical pass | `fixed` | [check_42_powered_doors](../../runs/check_42_powered_doors/result.json), [check_42_cavity_round](../../runs/check_42_cavity_round/result.json) |
| `skill_024` | `contract_032` | physical pass | `fixed` | [check_42_powered_doors](../../runs/check_42_powered_doors/result.json) |
| `skill_025` | `contract_033` | physical pass | `fixed` | [check_42_manual_doors](../../runs/check_42_manual_doors/result.json) |
| `skill_026` | `contract_034` | physical pass | `fixed` | [check_42_manual_doors](../../runs/check_42_manual_doors/result.json) |
| `skill_027` | `contract_035` | physical pass | `fixed` | [check_42_toy_carry](../../runs/check_42_toy_carry/result.json), [check_42_moving_place](../../runs/check_42_moving_place/result.json) |
| `skill_028` | `contract_036` | physical pass | `fixed` | [check_42_cavity_round](../../runs/check_42_cavity_round/result.json), [check_42_cavity_retry](../../runs/check_42_cavity_retry/result.json) |
| `skill_029` | `contract_037` | physical pass | `fixed` | [check_42_rect_pick](../../runs/check_42_rect_pick/result.json) |
| `skill_030` | `contract_038` | physical pass | `fixed` | [check_42_flat_edge](../../runs/check_42_flat_edge/result.json) |
| `skill_031` | `contract_039` | physical pass | `fixed` | [check_42_posture](../../runs/check_42_posture/result.json), [check_42_posture_corrected](../../runs/check_42_posture_corrected/result.json) |
| `skill_032` | `contract_040` | physical pass | `fixed` | [check_42_posture](../../runs/check_42_posture/result.json), [check_42_posture_corrected](../../runs/check_42_posture_corrected/result.json) |
| `skill_033` | `contract_041` | physical pass | `fixed` | [check_42_posture_corrected](../../runs/check_42_posture_corrected/result.json) |
| `skill_034` | `contract_042` | physical pass | `fixed` | [check_42_posture_corrected](../../runs/check_42_posture_corrected/result.json) |
| `skill_035` | `contract_043` | physical pass | `fixed` | [check_42_flat_edge](../../runs/check_42_flat_edge/result.json) |
| `skill_036` | `contract_044` | physical pass | `fixed` | [check_42_toy_carry](../../runs/check_42_toy_carry/result.json) |
| `skill_037` | `contract_045` | physical pass | `fixed` | [check_42_upright_place](../../runs/check_42_upright_place/result.json) |
| `skill_038` | `contract_046` | physical pass | `fixed` | [node_contract_near_apple](../../runs/node_contract_near_apple/result.json) |
| `skill_039` | `contract_047` | physical pass | `fixed` | [node_contract_upright_near_apple_threshold20](../../runs/node_contract_upright_near_apple_threshold20/result.json) |
| `skill_040` | `contract_048` | physical pass | `fixed` | [node_contract_heat_wait](../../runs/node_contract_heat_wait/result.json) |
| `skill_041` | `contract_049` | physical pass | `fixed` | [check_42_toy_carry](../../runs/check_42_toy_carry/result.json) |
| `skill_042` | `contract_050` | physical pass | `fixed` | [check_42_toy_carry](../../runs/check_42_toy_carry/result.json) |
| `skill_043` | `contract_051` | physical pass | `fixed` | [check_50_base](../../runs/check_50_base/result.json) |
| `skill_044` | `contract_052` | physical pass | `fixed` | [check_50_base](../../runs/check_50_base/result.json) |
| `skill_045` | `contract_053` | physical pass | `fixed` | [check_50_rear_push](../../runs/check_50_rear_push/result.json) |
| `skill_046` | `contract_054` | physical pass | `fixed` | [check_50_top_drag_green_fixed](../../runs/check_50_top_drag_green_fixed/result.json) |
| `skill_047` | `contract_055` | physical pass | `fixed` | [check_50_manual](../../runs/check_50_manual/result.json) |
| `skill_048` | `contract_056` | physical pass | `fixed` | [check_50_manual](../../runs/check_50_manual/result.json) |
| `skill_049` | `contract_057` | physical pass | `fixed` | [check_50_floor_ready_near](../../runs/check_50_floor_ready_near/result.json) |
| `skill_050` | `contract_058` | physical pass | `fixed` | [check_50_microwave_clear](../../runs/check_50_microwave_clear/result.json) |

**Physical passes: 46/50.** Remaining: 4.

Full observations, failures, and scene paths are in [node_contract_smoke.json](node_contract_smoke.json). Remaining blockers are in [FINDINGS.md](FINDINGS.md).
