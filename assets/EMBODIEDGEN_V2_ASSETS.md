# EmbodiedGen V2 task assets

The 12 objects in [`embodiedgen_v2_replacements.json`](embodiedgen_v2_replacements.json) are textured EmbodiedGen V2 meshes. Each asset lives in `assets/asset3d/<name>/result/` with a source URDF, visual OBJ, collision OBJ, MTL, texture, and a mesh render. `assets/custom_assets.json` records physical size, mass, collider class, prompt, and generator. `annotations/assets.json` and `usd/assets/` are produced from those sources.

The assets extend the **existing house** through [`recycle_and_store`](../task_specs/recycle_and_store.json), [`organize_utility_items`](../task_specs/organize_utility_items.json), and the [`kitchen_pot`](../scene_specs/kitchen_pot.json) demo. The small storage bin is available as a scene variant; it is not present in the default task scenes.

| Asset | Target size (cm) | Scene role |
| --- | --- | --- |
| `foam_cube` | 6 × 6 × 6 | recycling floor object |
| `soda_can` | 6.6 × 6.6 × 12 | recycling TV stand object |
| `snack_carton` | 6 × 11 × 17 | recycling TV stand object |
| `small_storage_bin` | 22 × 17 × 9 | optional storage target |
| `wide_storage_bin` | 34 × 30 × 14 | recycling bookcase target |
| `juice_bottle` | 5.8 × 5.8 × 18 | utility task TV stand object |
| `plastic_cup` | 8 × 8 × 9.5 | utility task table object |
| `paperback_book` | 18 × 12 × 2.5 | utility task table object |
| `tissue_box` | 14 × 9 × 6 | utility task TV stand object |
| `rolling_pin` | 22 × 4.6 × 4.6 | utility task side table object |
| `shallow_sorting_tray` | 27 × 20 × 5.5 | utility task bookcase target |
| `handled_cooking_pot` | 26 × 30 × 16 | kitchen counter grasp demo |

`handled_cooking_pot` has an open body and two side handles. The asset annotation supplies a side-handle pinch and a rim alternative. It has no overhead bail; the earlier procedural pot did. Container wall annotations and grasp candidates describe geometric affordances, not a passed physical rollout.

## Rebuild from the V2 sources

Use the EmbodiedGen V2 environment for generation, with `GPT_PROVIDER=codex` if the local Codex provider is configured. The soda can uses the committed V2-generated [condition image](asset3d/soda_can/source.png) with `img3d-cli`; the other eleven use `text3d-cli`. The committed URDF and meshes make regeneration optional. The following commands register them, convert them to USD, fix material references, and rebuild the three scene layers:

```bash
python tools/generate_assets.py --batch assets/embodiedgen_v2_replacements.json --skip-generate --skip-convert
OMNI_KIT_ACCEPT_EULA=YES "$ISAACLAB_PYTHON" tools/prepare_assets.py --only foam_cube soda_can snack_carton small_storage_bin wide_storage_bin juice_bottle plastic_cup paperback_book tissue_box rolling_pin shallow_sorting_tray handled_cooking_pot --convert
OMNI_KIT_ACCEPT_EULA=YES "$ISAACLAB_PYTHON" tools/fix_textures.py
OMNI_KIT_ACCEPT_EULA=YES "$ISAACLAB_PYTHON" tools/build_tasks.py --spec task_specs/recycle_and_store.json --seed 0
OMNI_KIT_ACCEPT_EULA=YES "$ISAACLAB_PYTHON" tools/build_tasks.py --spec task_specs/organize_utility_items.json --seed 0
OMNI_KIT_ACCEPT_EULA=YES "$ISAACLAB_PYTHON" tools/build_tasks.py --spec scene_specs/kitchen_pot.json --out scenes/kitchen_pot --seed 0
```

To generate an individual source again, use `python tools/generate_assets.py --name ... --prompt ... --size ... --mass ...`, or pass the batch manifest without `--skip-generate`. EmbodiedGen V2 outputs should be visually inspected before replacing a committed asset, since the same prompt can produce different geometry. The source scale is corrected in `tools/prepare_assets.py`; its `target_size` setting preserves the intended X/Y/Z footprint for upright assets. The book and tissue box use explicit X/Y/Z sizes. The rolling pin is rotated to a flat resting pose and scaled to a 22 cm longest side.

All three seed-0 scenes passed three-second stability checks after `tools/settle_scene.py`, `tools/check_scene.py`, and `tools/annotate_scene.py`. Contract results from the **previous procedural meshes** are retained as historical evidence in [`FINDINGS.md`](../skill_library/verification/FINDINGS.md); they do not establish that these V2 meshes have passed the same grasps. Task completion requires a fresh rollout on the rebuilt scenes.
