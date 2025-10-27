#!/bin/bash
# Start vLLM with Mistral 7B - MINIMAL memory usage
# For stubborn 12GB VRAM

set -e

echo "======================================================================"
echo "  Starting vLLM with Mistral 7B (Minimal Memory Mode)"
echo "======================================================================"
echo ""
echo "This will use:"
echo "  - Only 60% of GPU VRAM (~7GB)"
echo "  - Small context window (2K tokens)"
echo "  - Single sequence at a time"
echo "  - Should NOT OOM!"
echo ""
echo "Starting server on http://localhost:8000"
echo ""

# Ultra-conservative settings:
vllm serve mistralai/Mistral-7B-Instruct-v0.2 \
  --dtype half \
  --gpu-memory-utilization 0.60 \
  --max-model-len 2048 \
  --max-num-batched-tokens 1024 \
  --max-num-seqs 1 \
  --port 8000

# To stop: Press Ctrl+C

