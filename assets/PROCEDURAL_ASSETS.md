# New deterministic props

`tools/generate_procedural_assets.py` builds five physical meshes: a 6 cm foam cube, a 12 cm can, a 17 cm snack carton, a 22 cm open storage bin, and a 34 cm wide storage bin. The mesh, collision mesh, URDF, and `assets/custom_assets.json` are generated together. `tools/prepare_assets.py` supplies real size, mass, top or rim grasp annotations, and simulator USD.

```bash
/home/all/miniforge3/envs/isaaclab/bin/python tools/generate_procedural_assets.py
OMNI_KIT_ACCEPT_EULA=YES /home/all/miniforge3/envs/isaaclab/bin/python tools/prepare_assets.py --only foam_cube soda_can snack_carton small_storage_bin wide_storage_bin --convert
OMNI_KIT_ACCEPT_EULA=YES /home/all/miniforge3/envs/isaaclab/bin/python tools/build_tasks.py --spec task_specs/recycle_and_store.json --seed 0
```

The props broaden the nouns and geometry available to existing pick, push, place, and container policies. Mesh generation and annotation alone do not establish a physical policy pass. Check the task scene and run Contract smoke plans before using a prop as verified evidence.

The `recycle_and_store` task uses the wide bin. A measured test with the small bin picked the soda can but missed the container after release (`runs/check_local_can_bin/result.json`), so the narrow bin is not treated as a verified three-item receptacle.

The wide bin has a 14 cm rim. The existing container policy releases above rims taller than 12 cm; a shorter-rim prototype was pushed about 20 cm during the in-bin lowering route (`runs/check_wide_bin_can/result.json`).

A revised GT container policy first lifts a held object above the rim, translates above the opening, then releases it. A physical `soda_can` → `wide_storage_bin` test passed `contract_014`, reported `inside=true`, and measured **0.000 m** container shift (`runs/check_tall_bin_prelift/result.json`). This is one verified noun pair; it does not by itself prove the complete three-object task. The saved six-node control graph is in `skill_library/examples/recycle_and_store.skill_subgraph.json` with explicit noun bindings in the adjacent file.

A complete six-node control run is still incomplete: after the first can is inserted, navigation to pick the snack carton cannot fold the empty arm at the bookcase (`runs/recycle_control_exit_exact/result.json`). The new task is a reproducible scene and coverage target, not a completed task demonstration.
