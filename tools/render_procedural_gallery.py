"""Append the 12 procedural mesh previews to media/assets_gallery.jpg.

Requires Blender 2.93 and Pillow. Run: python tools/render_procedural_gallery.py
The first four rows are the existing EmbodiedGen gallery; rerunning is idempotent.
Preview colors are presentation materials applied to the committed OBJ meshes.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / "media/assets_gallery.jpg"
NAMES = (
    "foam_cube", "soda_can", "snack_carton", "small_storage_bin", "wide_storage_bin", "juice_bottle",
    "plastic_cup", "paperback_book", "tissue_box", "rolling_pin", "shallow_sorting_tray", "handled_cooking_pot",
)
COLORS = (
    (0.74, 0.78, 0.85), (0.62, 0.67, 0.72), (0.75, 0.67, 0.54),
    (0.58, 0.64, 0.66), (0.49, 0.58, 0.64), (0.73, 0.81, 0.84),
    (0.82, 0.84, 0.84), (0.69, 0.51, 0.42), (0.81, 0.74, 0.61),
    (0.68, 0.50, 0.34), (0.64, 0.70, 0.72), (0.43, 0.47, 0.51),
)
LABELS = (
    "top_pinch", "top_pinch", "top_pinch", "rim_pinch_rect", "rim_pinch_rect", "top_pinch",
    "rim_pinch", "edge_pinch*", "edge_pinch*", "top_pinch+edge*", "rim_pinch_rect", "top_pinch+handle_pinch",
)


def render_tiles(out_dir: Path) -> None:
    import bpy
    from mathutils import Vector

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.use_gtao = True
    scene.eevee.gtao_distance = 3
    scene.render.film_transparent = True
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.camera = None
    world = bpy.data.worlds.new("gallery_world")
    world.use_nodes = True
    world.node_tree.nodes.get("Background").inputs["Color"].default_value = (0.65, 0.65, 0.65, 1)
    world.node_tree.nodes.get("Background").inputs["Strength"].default_value = 0.8
    scene.world = world

    for name, color in zip(NAMES, COLORS):
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete(use_global=False)
        mesh = ROOT / "assets/asset3d" / name / "result/mesh" / f"{name}.obj"
        if not mesh.is_file():
            raise FileNotFoundError(mesh)
        bpy.ops.import_scene.obj(filepath=str(mesh), use_image_search=False, axis_forward="-Y", axis_up="Z")
        objects = [obj for obj in scene.objects if obj.type == "MESH"]
        if not objects:
            raise RuntimeError(f"No geometry imported for {name}")
        material = bpy.data.materials.new(name + "_gallery")
        material.diffuse_color = (*color, 1)
        material.use_nodes = True
        bsdf = material.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (*color, 1)
        bsdf.inputs["Roughness"].default_value = 0.62
        bsdf.inputs["Metallic"].default_value = 0.35 if name in {"soda_can", "handled_cooking_pot"} else 0.0
        for obj in objects:
            obj.data.materials.clear()
            obj.data.materials.append(material)
        coords = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
        lo = Vector(tuple(min(p[i] for p in coords) for i in range(3)))
        hi = Vector(tuple(max(p[i] for p in coords) for i in range(3)))
        center = (lo + hi) * 0.5
        scale = max(hi - lo)
        camera_data = bpy.data.cameras.new(name + "_camera")
        camera = bpy.data.objects.new(name + "_camera", camera_data)
        scene.collection.objects.link(camera)
        direction = Vector((2.6, -3.4, 2.7)).normalized()
        camera.location = center + direction * scale * 5
        camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera_data.type = "ORTHO"
        camera_data.ortho_scale = scale * 1.65
        scene.camera = camera
        for light_name, direction, energy, size in (
            ("key", Vector((-2, -3, 5)), 250, 4),
            ("fill", Vector((3, 2, 3)), 170, 4),
        ):
            data = bpy.data.lights.new(light_name, "AREA")
            light = bpy.data.objects.new(light_name, data)
            scene.collection.objects.link(light)
            light.location = center + direction.normalized() * scale * 5
            data.energy = energy * scale * scale
            data.size = size * scale
        scene.render.filepath = str(out_dir / f"{name}.png")
        bpy.ops.render.render(write_still=True)


def compose(out_dir: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont

    tile = 220
    old_rows = 4
    with Image.open(GALLERY) as original:
        if original.width != 6 * tile or original.height < old_rows * tile:
            raise ValueError(f"Unexpected old gallery size: {original.size}")
        gallery = Image.new("RGB", (6 * tile, 6 * tile), "black")
        gallery.paste(original.convert("RGB").crop((0, 0, 6 * tile, old_rows * tile)))
    label_font = ImageFont.truetype("DejaVuSansMono.ttf", 13)
    grasp_font = ImageFont.truetype("DejaVuSansMono.ttf", 11)
    draw = ImageDraw.Draw(gallery)
    for i, (name, grasp) in enumerate(zip(NAMES, LABELS)):
        x = (i % 6) * tile
        y = (old_rows + i // 6) * tile
        with Image.open(out_dir / f"{name}.png") as rendered:
            rgba = rendered.convert("RGBA")
            alpha = rgba.getchannel("A")
            bounds = alpha.getbbox()
            if bounds is None:
                raise ValueError(f"Empty render for {name}")
            rgba = rgba.crop(bounds)
            rgba.thumbnail((190, 160), Image.Resampling.LANCZOS)
            px = x + (tile - rgba.width) // 2
            py = y + (175 - rgba.height) // 2
            gallery.paste(rgba, (px, py), rgba)
        draw.text((x + 5, y + 183), name, font=label_font, fill=(230, 230, 230))
        draw.text((x + 5, y + 203), grasp, font=grasp_font, fill=(142, 213, 118))
    gallery.save(GALLERY, quality=94, subsampling=0)
    print(f"Updated {GALLERY} with {len(NAMES)} procedural assets")


def main() -> None:
    import subprocess
    import tempfile

    if "--tiles" in sys.argv:
        render_tiles(Path(sys.argv[-1]))
        return
    with tempfile.TemporaryDirectory(prefix="zeno-gallery-") as temporary:
        cmd = ["blender", "-b", "-noaudio", "--python", str(Path(__file__).resolve()), "--", "--tiles", temporary]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stdout[-3000:] + "\n" + result.stderr[-3000:])
        compose(Path(temporary))


if __name__ == "__main__":
    main()
