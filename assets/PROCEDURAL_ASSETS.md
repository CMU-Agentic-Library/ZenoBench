# Deterministic procedural assets

`tools/generate_procedural_assets.py` produces **11 real-size assets** with visual and collision OBJ meshes, URDFs, source registry entries and a reproducible generator. `tools/prepare_assets.py` converts them to simulator USD and writes `annotations/assets.json` grasp and container geometry. These assets use geometric meshes rather than EmbodiedGen textures.

| Asset | Size (cm) | Annotated contact route | Example scene |
| --- | --- | --- | --- |
| `foam_cube` | 6 × 6 × 6 | top pinch | `recycle_and_store`, floor |
| `soda_can` | 6.6 × 6.6 × 12 | top pinch | `recycle_and_store`, TV stand |
| `snack_carton` | 6 × 11 × 17 | top pinch | `recycle_and_store`, TV stand |
| `small_storage_bin` | 22 × 17 × 9 | rectangular rim pinch | available scene variant |
| `wide_storage_bin` | 34 × 30 × 14 | rectangular rim pinch | `recycle_and_store`, bookcase target |
| `juice_bottle` | 5.8 × 5.8 × 18 | top pinch | `organize_utility_items`, TV stand |
| `plastic_cup` | 8 × 8 × 9.5 | round rim pinch | `organize_utility_items`, side dining table |
| `paperback_book` | 18 × 12 × 2.5 | push to edge, then pinch | `organize_utility_items`, dining table |
| `tissue_box` | 14 × 9 × 6 | push to edge, then pinch | `organize_utility_items`, TV stand |
| `rolling_pin` | 22 × 4.4 × 4.4 | top pinch or edge route | `organize_utility_items`, side dining table |
| `shallow_sorting_tray` | 27 × 20 × 5.5 | rectangular rim pinch | `organize_utility_items`, bookcase target |

```bash
$ISAACLAB_PYTHON tools/generate_procedural_assets.py
OMNI_KIT_ACCEPT_EULA=YES $ISAACLAB_PYTHON tools/prepare_assets.py --only foam_cube soda_can snack_carton small_storage_bin wide_storage_bin juice_bottle plastic_cup paperback_book tissue_box rolling_pin shallow_sorting_tray --convert
OMNI_KIT_ACCEPT_EULA=YES $ISAACLAB_PYTHON tools/build_tasks.py --spec task_specs/recycle_and_store.json --seed 0
OMNI_KIT_ACCEPT_EULA=YES $ISAACLAB_PYTHON tools/build_tasks.py --spec task_specs/organize_utility_items.json --seed 0
```

The committed task layers, annotations and [scene checks](../tasks/organize_utility_items/check/check.json) are ready to use; rebuilds additionally need `tools/settle_scene.py` and `tools/annotate_scene.py` as described in [the task guide](../docs/README.md). Both seed-0 scenes passed three-second physics stability checks. The `organize_utility_items` scene contains all six assets from the second batch, with the shallow tray as a task target. Its [12-node saved graph](../skill_library/examples/organize_utility_items.skill_subgraph.json) and [noun bindings](../skill_library/examples/organize_utility_items.bindings.json) compile as an upper-layer plan, but the full graph has not been physically executed.

**Physical policy evidence is narrower than scene validity.** Separate Contract runs picked `foam_cube`, `soda_can` and `snack_carton` from the first scene; `soda_can` then passed `contract_014` into `wide_storage_bin` with `inside=true` and 0.000 m measured bin shift (`runs/check_tall_bin_prelift/result.json`). A fresh `juice_bottle` pick passed `contract_012` in the new scene (`runs/check_new_juice_bottle_pick/result.json`). The new cup, book, tissue box, rolling pin and tray have mesh/annotation and scene checks, but no successful object-specific Contract rollout yet. The full three-object `recycle_and_store` graph remains incomplete because the arm cannot tuck at the bookcase after the first insertion ([finding](../skill_library/verification/FINDINGS.md)).

For `plastic_cup`, the rim-pick Contract was attempted from both the default base pose and a local park. The first run found no base path; the second found no collision-free joint path into the pre-grasp. Both failures are recorded in [the physical findings](../skill_library/verification/FINDINGS.md). The new 12-node task graph has not been run end to end.

The small bin is an available variant; a measured can→small-bin attempt missed the container after release (`runs/check_local_can_bin/result.json`). The wide bin's 14 cm rim uses a prelift route; a shorter-rim prototype was pushed during an in-bin lowering route (`runs/check_wide_bin_can/result.json`). Those negative runs remain recorded rather than being treated as success.
