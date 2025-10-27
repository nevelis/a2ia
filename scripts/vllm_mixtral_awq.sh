#!/bin/bash
# Start vLLM with Mixtral 8x7B (AWQ Quantized) - for 12GB VRAM
# This is the ADVANCED option with 4-bit quantization

set -e

echo "======================================================================"
echo "  Starting vLLM with Mixtral 8x7B (AWQ 4-bit Quantized)"
echo "======================================================================"
echo ""
echo "⚠️  WARNING: This is at the edge of 12GB VRAM capacity"
echo ""
echo "This model will:"
echo "  - Use ~10-11GB VRAM (very tight fit)"
echo "  - Support 2-4K context length"
echo "  - Be slower than Mistral 7B"
echo "  - More powerful but harder to run"
echo ""
echo "If you get OOM errors, use vllm_mistral7b.sh instead"
echo ""
echo "Starting server on http://localhost:8000"
echo ""

vllm serve TheBloke/Mixtral-8x7B-Instruct-v0.1-AWQ \
  --quantization awq \
  --dtype half \
  --max-model-len 2048 \
  --gpu-memory-utilization 0.85 \
  --enable-chunked-prefill \
  --port 8000

# To stop: Press Ctrl+C

