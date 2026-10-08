"""One command from a text prompt (or a photo) to a sim-ready, annotated asset.

    python tools/generate_assets.py --name soda_can --prompt "an empty aluminium soda can" \
        --size 0.12 --mass 0.35 --tags can container
    python tools/generate_assets.py --name my_mug --image photos/mug.jpg --size 0.10 --mass 0.3 \
        --collider round_container --tags mug container
    python tools/generate_assets.py --batch assets/my_assets.json      # several at once (format below)

Steps (each can be skipped, see --help):
  1. generate   EmbodiedGen V2 text3d-cli / img3d-cli in the `embodiedgen` env
                -> assets/asset3d/<name>/result/<name>.urdf + textured mesh
  2. register   real size, mass, tags, collider -> assets/custom_assets.json
  3. convert    tools/prepare_assets.py --only <names> --convert (Isaac Lab python):
                real-size scaling, lay-flat, grasp annotation for the Zeno gripper
                -> annotations/assets.json, usd/assets/<name>.usd
  4. textures   tools/fix_textures.py (per-asset texture files)
Then use the asset in a task spec ("objects": {"can_1": {"asset": "soda_can", ...}}).

Environment:
  EMBODIEDGEN_ROOT    EmbodiedGen checkout (default ../EmbodiedGen)
  EMBODIEDGEN_PYTHON  python of the embodiedgen env; its bin/ must hold text3d-cli / img3d-cli
                      (default: `conda run -n embodiedgen`)
  ISAACLAB_PYTHON     Isaac Lab python (steps 3-4)

Batch file: {"soda_can": {"prompt": "...", "size": 0.12, "mass": 0.35, "tags": ["can"],
                          "collider": "solid", "lay_flat": false}, "my_mug": {"image": "...", ...}}
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CUSTOM = ROOT / "assets" / "custom_assets.json"
GEN = ROOT / "assets" / "asset3d"
COLLIDERS = ("solid", "round_container", "rect_container")


def eg_cmd(tool):
    py = os.environ.get("EMBODIEDGEN_PYTHON")
    if py:
        exe = Path(py).parent / tool
        return [str(exe)] if exe.exists() else [py, "-m", f"embodied_gen.scripts.{tool.replace('-', '_')}"]
    return ["conda", "run", "--no-capture-output", "-n", "embodiedgen", tool]


def run(cmd, cwd=None, env=None, check=True):
    print("+", " ".join(str(c) for c in cmd), flush=True)
    done = subprocess.run([str(c) for c in cmd], cwd=cwd, env=env)
    if check and done.returncode != 0:
        raise subprocess.CalledProcessError(done.returncode, cmd)
    return done.returncode


def generate(name, spec, retries):
    """EmbodiedGen into a scratch dir, then move <result>/ to assets/asset3d/<name>/result."""
    repo = Path(os.environ.get("EMBODIEDGEN_ROOT", ROOT.parent / "EmbodiedGen"))
    if not repo.exists():
        sys.exit(f"EmbodiedGen checkout not found at {repo}: set EMBODIEDGEN_ROOT")
    with tempfile.TemporaryDirectory(prefix=f"gen_{name}_") as tmp:
        tmp = Path(tmp)
        if spec.get("image"):
            img = Path(spec["image"]).resolve()
            code = run(eg_cmd("img3d-cli") + ["--image_path", img, "--n_retry", retries, "--output_root", tmp],
                       cwd=repo, check=False)
        else:
            code = run(eg_cmd("text3d-cli") + ["--prompts", spec["prompt"], "--asset_names", name,
                                               "--n_image_retry", retries, "--n_asset_retry", retries, "--n_pipe_retry", 1,
                                               "--seed_img", spec.get("seed", 0), "--output_root", tmp], cwd=repo,
                       check=False)
        urdfs = sorted(tmp.rglob("result/*.urdf"))
        if not urdfs:
            sys.exit(f"{name}: EmbodiedGen produced no URDF (see its log above)")
        if code:
            # The V2 CLIs can exit nonzero during teardown after saving a
            # complete result; the URDF and meshes are what matter here.
            print(f"{name}: generator exited with {code} after writing {urdfs[0]}", flush=True)
        res = urdfs[0].parent
        dst = GEN / name / "result"
        if dst.exists():
            shutil.rmtree(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(res, dst)
        u = dst / urdfs[0].name
        if u.name != f"{name}.urdf":
            u.rename(dst / f"{name}.urdf")
    print("GENERATED", dst, flush=True)


def register(name, spec):
    d = json.loads(CUSTOM.read_text()) if CUSTOM.exists() else {}
    c = spec.get("collider", "solid")
    if c not in COLLIDERS:
        sys.exit(f"{name}: collider must be one of {COLLIDERS}")
    d[name] = {"size": float(spec["size"]), "mass": float(spec["mass"]), "tags": list(spec.get("tags", [])),
               "collider": c, "lay_flat": bool(spec.get("lay_flat", False)),
               "urdf": f"assets/asset3d/{name}/result/{name}.urdf"}
    for key in ("body_fraction", "target_size", "generator", "prompt", "container_profile",
                "top_grasp", "handle_grasp", "handle_collider", "extra_handle_colliders", "knob_collider",
                "round_top"):
        if key in spec:
            d[name][key] = spec[key]
    CUSTOM.write_text(json.dumps(d, indent=1) + "\n")
    print("REGISTERED", name, d[name], flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--prompt", help="text-to-3D prompt")
    g.add_argument("--image", help="image-to-3D: a photo of the object")
    ap.add_argument("--size", type=float, help="longest extent, metres (the mesh is rescaled to it)")
    ap.add_argument("--mass", type=float, help="kg")
    ap.add_argument("--tags", nargs="*", default=[])
    ap.add_argument("--collider", default="solid", choices=COLLIDERS)
    ap.add_argument("--lay-flat", action="store_true", help="rest on the largest face (books, pens)")
    ap.add_argument("--batch", help="JSON file with several assets")
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--skip-generate", action="store_true", help="reuse assets/asset3d/<name>/result")
    ap.add_argument("--skip-convert", action="store_true", help="only generate + register")
    args = ap.parse_args()

    if args.batch:
        specs = {k: v for k, v in json.loads(Path(args.batch).read_text()).items() if not k.startswith("_")}
    else:
        if not (args.name and args.size and args.mass and (args.prompt or args.image or args.skip_generate)):
            ap.error("--name, --size, --mass and --prompt/--image are required (or --batch)")
        specs = {args.name: {"prompt": args.prompt, "image": args.image, "size": args.size, "mass": args.mass,
                             "tags": args.tags, "collider": args.collider, "lay_flat": args.lay_flat}}

    for name, spec in specs.items():
        if not args.skip_generate:
            generate(name, spec, args.retries)
        elif not (GEN / name / "result" / f"{name}.urdf").exists():
            sys.exit(f"{name}: --skip-generate but assets/asset3d/{name}/result/{name}.urdf is missing")
        register(name, spec)
    if args.skip_convert:
        return

    py = os.environ.get("ISAACLAB_PYTHON", sys.executable)
    env = dict(os.environ, OMNI_KIT_ACCEPT_EULA="YES")
    run([py, ROOT / "tools/prepare_assets.py", "--only", *specs, "--convert"], cwd=ROOT, env=env)
    run([py, ROOT / "tools/fix_textures.py"], cwd=ROOT, env=env)

    anns = json.loads((ROOT / "annotations/assets.json").read_text())
    print("\nDONE")
    for name in specs:
        a = anns.get(name, {})
        print(f"  {name}: size {a.get('size')} m, grasps {[g['type'] for g in a.get('grasps', [])]}, "
              f"graspable_by_zeno {a.get('graspable_by_zeno')}, usd {a.get('usd')}")
    first = next(iter(specs))
    print(f'\nUse it in a task spec:  "objects": {{"{first}_1": {{"asset": "{first}", '
          f'"supports": ["tv_stand", "floor:living_room"]}}}}')


if __name__ == "__main__":
    main()
