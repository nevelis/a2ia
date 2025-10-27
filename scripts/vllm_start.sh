#!/bin/bash
# Quick start script for vLLM (Safe default: Mistral 7B)

set -e

echo "======================================================================"
echo "  vLLM Quick Start"
echo "======================================================================"
echo ""
echo "Choose your model:"
echo "  1. Mistral 7B      - Safe, fast, recommended for 12GB VRAM"
echo "  2. Mixtral 8x7B    - Powerful but tight fit, may OOM"
echo ""

# Auto-select Mistral 7B as safe default
if [ "$1" == "mixtral" ]; then
    echo "Starting Mixtral 8x7B (AWQ)..."
    exec ./vllm_mixtral_awq.sh
else
    echo "Starting Mistral 7B (recommended)..."
    exec ./vllm_mistral7b.sh
fi

