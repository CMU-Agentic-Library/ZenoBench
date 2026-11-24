#!/usr/bin/env bash
# Serve Qwen3.5-4B with vLLM (OpenAI-compatible) for the baselines and Graph Manager.
# Same flags as baseline/graph_manager/examples/vllm-qwen3.5-4b.compose.yml, so one server serves both.
#
#   bash baseline/serve_qwen.sh                 # foreground; Ctrl-C stops it
#   SHIFT_VLLM_GPU_UTIL=0.40 bash baseline/serve_qwen.sh
#
# Environment (defaults in brackets):
#   VLLM_PY        python of the vLLM venv   [../.venvs/vllm-qwen/bin/python]
#   QWEN_WEIGHTS   model directory           [../models/Qwen3.5-4B]
#   SHIFT_VLLM_PORT                          [8001]
#   SHIFT_VLLM_GPU_UTIL  share of GPU memory [0.45: leaves room for Isaac Sim on the same 24 GB card]
set -euo pipefail
HERE=$(cd "$(dirname "$0")/../.." && pwd)            # physical_harnessing/
VLLM_PY=${VLLM_PY:-$HERE/.venvs/vllm-qwen/bin/python}
QWEN_WEIGHTS=${QWEN_WEIGHTS:-$HERE/models/Qwen3.5-4B}
exec "$VLLM_PY" -m vllm.entrypoints.openai.api_server \
  --model="$QWEN_WEIGHTS" \
  --served-model-name=qwen3.5-4b \
  --host=0.0.0.0 \
  --port="${SHIFT_VLLM_PORT:-8001}" \
  --gpu-memory-utilization="${SHIFT_VLLM_GPU_UTIL:-0.45}" \
  --max-model-len=32768 \
  --reasoning-parser=qwen3 \
  --enable-auto-tool-choice \
  --tool-call-parser=qwen3_coder \
  --tool-strict-level=parameter
