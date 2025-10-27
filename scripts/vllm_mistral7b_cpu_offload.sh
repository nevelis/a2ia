#!/bin/bash
# Start vLLM with Mistral 7B + CPU Offloading
# For 12GB VRAM that keeps OOMing

set -e

echo "======================================================================"
echo "  Starting vLLM with Mistral 7B + CPU Offloading"
echo "======================================================================"
echo ""
echo "This will use:"
echo "  - ~8GB GPU VRAM (reduced from 12GB)"
echo "  - ~8-10GB RAM for offloaded layers"
echo "  - Will be slower but should work!"
echo ""
echo "Starting server on http://localhost:8000"
echo ""

# Key settings for CPU offloading:
# --gpu-memory-utilization 0.70 = Only use 70% of VRAM
# --swap-space 16 = 16GB swap space for offloading
# --max-model-len 4096 = Smaller context to save memory
# --max-num-batched-tokens 2048 = Smaller batches

vllm serve mistralai/Mistral-7B-Instruct-v0.2 \
  --dtype half \
  --gpu-memory-utilization 0.70 \
  --swap-space 16 \
  --max-model-len 4096 \
  --max-num-batched-tokens 2048 \
  --port 8000

# To stop: Press Ctrl+C

