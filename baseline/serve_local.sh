#!/usr/bin/env bash
# vLLM 0.32.0. Select the GPU with CUDA_VISIBLE_DEVICES before starting the service.
# Usage: bash baseline/serve_local.sh MODEL_ID WEIGHTS_DIRECTORY PORT [GPU_MEMORY_FRACTION]
set -euo pipefail
model=${1:?model id}
weights=${2:?pinned weight directory}
port=${3:?loopback port}
util=${4:-0.80}
here=$(cd "$(dirname "$0")" && pwd)
case "$model" in
    qwen3.5-4b|qwen3.5-27b)
        chat=(--reasoning-parser qwen3 --tool-call-parser qwen3_coder
              --default-chat-template-kwargs '{"enable_thinking":false}')
        ;;
    internvl3.5-8b)
        chat=(--chat-template "$here/internvl_tools.jinja" --chat-template-content-format openai
              --tool-call-parser hermes)
        ;;
    *) echo "Unknown local model: $model" >&2; exit 2 ;;
esac
export HF_HUB_OFFLINE=1
export VLLM_USE_FLASHINFER_SAMPLER=0
exec "${VLLM_PY:-python3}" -m vllm.entrypoints.openai.api_server \
    --model "$weights" --served-model-name "$model" --host 127.0.0.1 --port "$port" \
    --dtype bfloat16 --max-model-len 32768 --max-num-seqs 16 --gpu-memory-utilization "$util" \
    --generation-config vllm --override-generation-config '{"temperature":0,"max_new_tokens":4096}' \
    --enable-auto-tool-choice --tool-strict-level parameter "${chat[@]}"
