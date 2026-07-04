#!/bin/bash
set -euo pipefail

MODEL="/Users/nana-520/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct-GGUF/snapshots/bb5d59e06d9551d752d08b292a50eb208b07ab1f/qwen2.5-7b-instruct-q3_k_m.gguf"
BIN="/Users/nana-520/llama.cpp-master/build/bin/llama-server"

# 【优化核心逻辑】
# -ngl 24: 仅将 24 个主要层卸载到 GPU，留下 4 个长尾层给 CPU，彻底杜绝 Metal OOM 降级。
# --ctx-size 1024: 强制缩减上下文至 1024，极大压低 KV Cache 显存侵占，为 Decode 吐字腾出物理带宽。
# --flash-attn: 激活闪电注意力机制，降低计算复杂度。
exec "$BIN" \
  -m "$MODEL" \
  --port 8080 \
  --host 0.0.0.0 \
  -ngl 24 \
  -t 4 \
  -tb 4 \
  -b 512 \
  --ctx-size 1024 \
  -fa on \
  --mlock
