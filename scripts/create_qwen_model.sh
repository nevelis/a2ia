#!/bin/bash
# Create custom A2IA Qwen model with correct ChatML template

set -e

echo "======================================================================"
echo "  Creating A2IA Qwen Model (with Tool Support)"
echo "======================================================================"
echo ""

# Check if base model exists
if ! ollama list | grep -q "qwen2.5:7b"; then
    echo "Base model not found. Pulling qwen2.5:7b..."
    ollama pull qwen2.5:7b
    echo ""
fi

echo "Creating a2ia-qwen from Modelfile-qwen..."
ollama create a2ia-qwen -f Modelfile-qwen

echo ""
echo "======================================================================"
echo "✅ Model created successfully!"
echo "======================================================================"
echo ""
echo "Usage:"
echo ""
echo "  # Test the model"
echo "  ollama run a2ia-qwen"
echo ""
echo "  # Use with A2IA CLI (with native tool calling support!)"
echo "  a2ia-cli --model a2ia-qwen"
echo ""
echo "  # Use with debugging"
echo "  a2ia-cli --model a2ia-qwen --debug"
echo ""
echo "======================================================================"
echo ""
echo "Model details:"
ollama show a2ia-qwen
echo ""

