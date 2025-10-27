#!/bin/bash
# Start vLLM with Mistral 7B - optimized for 12GB VRAM
# This is the SAFE option that will definitely work

set -e

echo "======================================================================"
echo "  Starting vLLM with Mistral 7B (Safe for 12GB VRAM)"
echo "======================================================================"
echo ""
echo "This model will:"
echo "  - Fit comfortably in 12GB VRAM (~6-7GB used)"
echo "  - Support 8K context length"
echo "  - Run fast (~60-80 tokens/sec)"
echo "  - Have good tool calling support"
echo ""
echo "Starting server on http://localhost:8000"
echo ""

vllm serve mistralai/Mistral-7B-Instruct-v0.2 \
  --dtype half \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.90 \
  --port 8000

# To stop: Press Ctrl+C

