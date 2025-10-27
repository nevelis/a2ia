#!/bin/bash
# Start vLLM with Phi-3 Mini (3.8B) - TINY model for testing
# For when even 7B won't fit

set -e

echo "======================================================================"
echo "  Starting vLLM with Phi-3 Mini (3.8B parameters)"
echo "======================================================================"
echo ""
echo "This is a TINY model that will definitely fit:"
echo "  - Only ~3.8B parameters (vs 7B)"
echo "  - Uses ~3-4GB VRAM"
echo "  - Fast and efficient"
echo "  - Good for testing vLLM setup"
echo ""
echo "Starting server on http://localhost:8000"
echo ""

vllm serve microsoft/Phi-3-mini-4k-instruct \
  --dtype half \
  --trust-remote-code \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.80 \
  --port 8000

# To stop: Press Ctrl+C

