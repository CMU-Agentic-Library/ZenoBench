#!/bin/bash
# Regenerate the two poor first-batch results (pencil came out as a block with
# an eraser, banana upright/peeled), after batch 2 has finished (memory).
set -e
# run inside the `embodiedgen` conda env, from the EmbodiedGen repository root
cd "${EMBODIEDGEN_ROOT:?set EMBODIEDGEN_ROOT to your EmbodiedGen checkout}"
OUT="$(cd "$(dirname "$0")" && pwd)"
mv "$OUT"/asset3d/pencil "$OUT"/asset3d/_rejected_pencil_v1 || true
mv "$OUT"/asset3d/banana "$OUT"/asset3d/_rejected_banana_v1 || true
text3d-cli \
  --prompts "a long thin sharpened yellow wooden pencil lying flat on a table" \
            "a single whole curved yellow banana lying on its side, unpeeled" \
  --asset_names pencil banana \
  --n_image_retry 2 --n_asset_retry 2 --n_pipe_retry 1 --seed_img 3 \
  --output_root "$OUT"
