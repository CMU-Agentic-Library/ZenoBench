"""Extend the existing asset gallery with EmbodiedGen V2 mesh renders.

Run after V2 generation and annotation: python tools/render_asset_gallery.py
The first four rows are retained from the existing gallery; rerunning is idempotent.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / "media/assets_gallery.jpg"
NAMES = (
    "foam_cube", "soda_can", "snack_carton", "small_storage_bin", "wide_storage_bin", "juice_bottle",
    "plastic_cup", "paperback_book", "tissue_box", "rolling_pin", "shallow_sorting_tray", "handled_cooking_pot",
)
VIEW = {name: "0000" for name in NAMES}


def grasp_label(asset: dict) -> str:
    names = []
    for grasp in asset.get("grasps", []):
        kind = grasp["type"]
        if kind == "edge_pinch_after_push":
            kind = "edge_pinch*"
        if kind not in names:
            names.append(kind)
    return "+".join(names) if names else "not graspable"


def main() -> None:
    tile = 220
    old_rows = 4
    assets = json.loads((ROOT / "annotations/assets.json").read_text())
    with Image.open(GALLERY) as original:
        if original.width != 6 * tile or original.height < old_rows * tile:
            raise ValueError(f"Unexpected gallery size: {original.size}")
        gallery = Image.new("RGB", (6 * tile, 6 * tile), "black")
        gallery.paste(original.convert("RGB").crop((0, 0, 6 * tile, old_rows * tile)))
    label_font = ImageFont.truetype("DejaVuSansMono.ttf", 13)
    grasp_font = ImageFont.truetype("DejaVuSansMono.ttf", 11)
    draw = ImageDraw.Draw(gallery)
    for index, name in enumerate(NAMES):
        x = (index % 6) * tile
        y = (old_rows + index // 6) * tile
        render = ROOT / "assets/asset3d" / name / "result/renders/image_color" / f"{VIEW[name]}.png"
        with Image.open(render) as image:
            rgb = image.convert("RGB")
            mask = ImageChops.difference(rgb, Image.new("RGB", rgb.size, "black")).convert("L")
            mask = mask.point(lambda value: 255 if value > 6 else 0)
            bounds = mask.getbbox()
            if bounds is None:
                raise ValueError(f"Empty V2 render: {render}")
            rgb = rgb.crop(bounds)
            rgb.thumbnail((190, 160), Image.Resampling.LANCZOS)
            gallery.paste(rgb, (x + (tile - rgb.width) // 2, y + (175 - rgb.height) // 2))
        draw.text((x + 5, y + 183), name, font=label_font, fill=(230, 230, 230))
        draw.text((x + 5, y + 203), grasp_label(assets[name]), font=grasp_font, fill=(142, 213, 118))
    gallery.save(GALLERY, quality=94, subsampling=0)
    print(f"Updated {GALLERY} with {len(NAMES)} EmbodiedGen V2 assets")


if __name__ == "__main__":
    main()
