# Kitchen pot demo

This scene adds a textured EmbodiedGen V2 `handled_cooking_pot` to the existing house's kitchen counter. It is separate from the ten canonical ZenoBench tasks. The generated pot has an open body and two **side handles**. Its source visual/collision OBJ, texture, URDF, converted USD, and grasp annotation are in the existing asset directories. The annotation offers a side-handle pinch and a round-rim route; geometry alone does not verify a lift.

- [Scene spec](../../scene_specs/kitchen_pot.json), [USD scene](scene.usd), [scene annotation](annotation.json)
- [Kitchen view](check/pot_close.png), [stability check](check/check.json)
- [Handle Contract smoke plan](pick_handle.plan.json), [bounded rim policy plan](pick_rim.plan.json)

The scene uses `kitchen_counter_surface`, the actual kitchen fixture support at 1.009 m. The older `kitchen_counter` repair support is lower and caused the wider V2 pot to spawn inside the fixture. This seed-0 scene now passes a three-second PhysX stability check (0 m pot and robot drift).

The earlier procedural pot had an overhead bail; its failed `contract_025` run is preserved as historical evidence in [physical findings](../../skill_library/verification/FINDINGS.md). On the V2 pot, the side-handle policy reaches the pregrasp/contact sequence but the fingers do not retain the pot through a measured lift (`runs/kitchen_pot_v2_tucked_handle_pick/result.json`). A collision-aware IK regression test covers the open space above the counter. A bounded `policy_011` rim attempt checked two candidates and found no reachable grasp (`runs/kitchen_pot_v2_rim_policy/result.json`). A physical lift remains unverified.

To rebuild from the committed V2 mesh sources (`ISAACLAB_PYTHON` points to Isaac Lab):

```bash
python tools/generate_assets.py --batch assets/embodiedgen_v2_replacements.json --skip-generate --skip-convert
OMNI_KIT_ACCEPT_EULA=YES "$ISAACLAB_PYTHON" tools/prepare_assets.py --only handled_cooking_pot --convert
OMNI_KIT_ACCEPT_EULA=YES "$ISAACLAB_PYTHON" tools/fix_textures.py
OMNI_KIT_ACCEPT_EULA=YES "$ISAACLAB_PYTHON" tools/build_tasks.py --spec scene_specs/kitchen_pot.json --out scenes/kitchen_pot --seed 0
OMNI_KIT_ACCEPT_EULA=YES "$ISAACLAB_PYTHON" tools/settle_scene.py scenes/kitchen_pot/scene.usd --seconds 5
OMNI_KIT_ACCEPT_EULA=YES "$ISAACLAB_PYTHON" tools/check_scene.py scenes/kitchen_pot/scene.usd --out scenes/kitchen_pot/check
OMNI_KIT_ACCEPT_EULA=YES "$ISAACLAB_PYTHON" tools/annotate_scene.py scenes/kitchen_pot/scene.usd scenes/kitchen_pot/annotation.json
OMNI_KIT_ACCEPT_EULA=YES "$ISAACLAB_PYTHON" tools/run_contracts.py --scene scenes/kitchen_pot/scene.usd --ann scenes/kitchen_pot/annotation.json --plan scenes/kitchen_pot/pick_handle.plan.json --out runs/kitchen_pot_v2_tucked_handle_pick --start-base -1.0 7.45 60
```
