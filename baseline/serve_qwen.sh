#!/usr/bin/env bash
# Serve Qwen3.5-4B with vLLM (OpenAI-compatible) for the baselines and Graph Manager.
# Same model flags as baseline/graph_manager/examples/vllm-qwen3.5-4b.compose.yml, so one server serves both.
#
#   bash baseline/serve_qwen.sh                 # foreground; Ctrl-C stops it
#   SHIFT_VLLM_GPU_UTIL=0.40 bash baseline/serve_qwen.sh
#
# Environment (defaults in brackets):
#   VLLM_PY        python of the vLLM venv   [../.venvs/vllm-qwen/bin/python]
#   QWEN_WEIGHTS   model directory           [../models/Qwen3.5-4B]
#   SHIFT_VLLM_PORT                          [8001]
#   SHIFT_VLLM_GPU_UTIL  share of GPU memory [0.60 ~ 14.7 GB: 9.3 GB weights + ~3 GB KV cache; 0.45 left no
#                        KV cache. The rest of the 24 GB card is for Isaac Sim]
#   SHIFT_VLLM_MAX_SEQS  concurrent requests [16: at most 2 simulators run at once]
set -euo pipefail
HERE=$(cd "$(dirname "$0")/../.." && pwd)            # physical_harnessing/
VLLM_PY=${VLLM_PY:-$HERE/.venvs/vllm-qwen/bin/python}
QWEN_WEIGHTS=${QWEN_WEIGHTS:-$HERE/models/Qwen3.5-4B}
export PATH="$(dirname "$VLLM_PY"):$PATH"            # ninja (kernel JIT) lives in the venv's bin
# the system nvcc (CUDA 12.2) cannot JIT FlashInfer's sampling kernels; use PyTorch sampling instead
export VLLM_USE_FLASHINFER_SAMPLER=${VLLM_USE_FLASHINFER_SAMPLER:-0}
exec "$VLLM_PY" -m vllm.entrypoints.openai.api_server \
  --model="$QWEN_WEIGHTS" \
  --served-model-name=qwen3.5-4b \
  --host=0.0.0.0 \
  --port="${SHIFT_VLLM_PORT:-8001}" \
  --gpu-memory-utilization="${SHIFT_VLLM_GPU_UTIL:-0.60}" \
  --max-model-len=32768 \
  --max-num-seqs="${SHIFT_VLLM_MAX_SEQS:-16}" \
  --reasoning-parser=qwen3 \
  --enable-auto-tool-choice \
  --tool-call-parser=qwen3_coder \
  --tool-strict-level=parameter
