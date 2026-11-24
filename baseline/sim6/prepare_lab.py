"""Prepare a separate, rigid-body Isaac Lab 2.3.2 checkout for Isaac Sim 6.0.0.1.

Run this in the Sim 6 Python environment. Source is the unpacked 2.3.2 wheel's
isaaclab directory (apps/ and source/). Put OUTPUT/source/isaaclab on PYTHONPATH.
"""

import argparse
import hashlib
import importlib.metadata as md
import json
from pathlib import Path
import shutil
import tomllib


def adapt(path, text, urdf):
    if path.suffix == ".kit":
        if path.name == "isaaclab.python.headless.rendering.kit":
            text = text.replace('"omni.kit.viewport.rtx" = {}',
                                '"omni.kit.viewport.rtx" = {}\n"omni.kit.hydra_texture" = {}')
        return text.replace('app.version = "5.1.0"', 'app.version = "6.0.0"').replace(
            '"isaacsim.asset.importer.urdf" = {version = "2.4.31", exact = true}',
            f'"isaacsim.asset.importer.urdf" = {{version = "{urdf}", exact = true}}')
    text = text.replace("import omni.physics.tensors.impl.api as physx", "import omni.physics.tensors.api as physx")
    if path.name == "deformable_object_data.py" and "from __future__ import annotations" not in text:
        text = text.replace("import weakref", "from __future__ import annotations\n\nimport weakref", 1)
    if path.name == "prims.py":
        text = text.replace("prim.HasAPI(PhysxSchema.PhysxDeformableBodyAPI)",
                            'prim.HasAPI("OmniPhysicsDeformableBodyAPI")')
    if path.name == "simulation_context.py":
        # Kit 6 can render sensors offscreen without creating a GUI viewport.
        anchor = '        self._offscreen_render = bool(self.carb_settings.get("/isaaclab/render/offscreen"))'
        text = text.replace(anchor, anchor + '\n        if self._offscreen_render:\n'
                            '            context = omni.usd.get_context()\n'
                            '            if "rtx" not in context.get_attached_hydra_engine_names():\n'
                            '                omni.usd.create_hydra_engine("rtx", context)')
        text = text.replace("            get_active_viewport().updates_enabled = False",
                            "            viewport = get_active_viewport()\n"
                            "            if viewport is not None:\n"
                            "                viewport.updates_enabled = False")
    if path.name == "app_launcher.py":
        anchor = "        self._app = SimulationApp(self._sim_app_config, experience=self._sim_experience_file)\n"
        options = ('        if os.environ.get("ZENO_SIM_GPU") and os.environ.get("CUDA_VISIBLE_DEVICES"):\n'
                   '            # CUDA sees one device; the Kit render index stays physical.\n'
                   '            if len(os.environ["CUDA_VISIBLE_DEVICES"].split(",")) == 1:\n'
                   '                self._sim_app_config["physics_gpu"] = 0\n'
                   '        if os.environ.get("ZENO_SIM_THREADS"):\n'
                   '            self._sim_app_config["limit_cpu_threads"] = int(os.environ["ZENO_SIM_THREADS"])\n')
        text = text.replace(anchor, options + anchor + "        import omni.physx\n"
                            "        from omni.physx.bindings._physx import acquire_physx_interface\n"
                            "        omni.physx.acquire_physx_interface = acquire_physx_interface\n")
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    # Kit accepts settings tables that reopen dotted keys. Python TOML only
    # needs the standard package header to identify the source release.
    experience = (source / "apps/isaaclab.python.headless.rendering.kit").read_text()
    lab_version = tomllib.loads(experience.partition("[dependencies]")[0])["package"]["version"]
    if lab_version != "2.3.2":
        raise ValueError(f"expected Isaac Lab 2.3.2, got {lab_version}")
    version = md.version("isaacsim")
    if version != "6.0.0.1":
        raise ValueError(f"expected Isaac Sim 6.0.0.1, got {version}")
    sim = Path(md.distribution("isaacsim").locate_file("isaacsim"))
    ext = sim / "exts/isaacsim.asset.importer.urdf/config/extension.toml"
    urdf = tomllib.loads(ext.read_text())["package"]["version"]
    curobo = md.distribution("nvidia-curobo")
    if curobo.version != "0.7.8":
        raise ValueError(f"expected cuRobo 0.7.8, got {curobo.version}")
    shutil.copytree(source, output, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    changes = {}
    for path in [*output.glob("apps/**/*.kit"), *output.glob("source/**/*.py")]:
        original = path.read_text()
        updated = adapt(path, original, urdf)
        if updated != original:
            path.write_text(updated)
            changes[str(path.relative_to(output))] = hashlib.sha256(updated.encode()).hexdigest()
    # Keep the compiled wheel intact. The overlay uses Sim 6 Warp's public
    # device conversion entry point and the same cuRobo CUDA libraries.
    overlay = output / "source/isaaclab/curobo"
    original_curobo = Path(curobo.locate_file("curobo"))
    shutil.copytree(original_curobo, overlay, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    path = overlay / "geom/sdf/world_mesh.py"
    updated = path.read_text().replace("wp.torch.device_from_torch(", "wp.device_from_torch(")
    path.write_text(updated)
    changes[str(path.relative_to(output))] = hashlib.sha256(updated.encode()).hexdigest()
    manifest = {"isaacsim": version, "isaaclab_wheel": lab_version, "curobo": curobo.version,
                "urdf_extension": urdf, "patched_files": changes}
    (output / "compatibility.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
