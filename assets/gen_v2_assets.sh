#!/bin/bash
# EmbodiedGen V2 text-to-3D for the task scenes (run from repo root).
set -e
# run inside the `embodiedgen` conda env, from the EmbodiedGen repository root
cd "${EMBODIEDGEN_ROOT:?set EMBODIEDGEN_ROOT to your EmbodiedGen checkout}"
OUT="$(cd "$(dirname "$0")" && pwd)"
text3d-cli \
  --prompts \
    "a single fresh red apple" \
    "a single ripe yellow banana" \
    "a single round orange fruit" \
    "an empty shallow round woven wicker fruit basket with an open top" \
    "an empty flat rectangular wooden serving tray with low raised rims" \
    "a closed spiral notebook with a plain blue cover" \
    "a black ballpoint pen" \
    "a yellow wooden pencil with a pink eraser" \
    "a closed hardcover book with a red cover" \
    "a closed hardcover book with a dark green cover" \
    "a closed paperback book with a blue cover" \
    "a small red toy car" \
    "a small brown teddy bear plush toy" \
    "a colorful wooden toy building block cube" \
    "a yellow rubber duck toy" \
    "an empty open-top wooden toy storage box without a lid" \
    "an empty open-top gray plastic storage basket" \
  --asset_names apple banana orange fruit_basket serving_tray notebook pen pencil \
    book_red book_green book_blue toy_car teddy_bear toy_block rubber_duck toy_box storage_basket \
  --n_image_retry 2 --n_asset_retry 2 --n_pipe_retry 1 --seed_img 0 \
  --output_root "$OUT"
