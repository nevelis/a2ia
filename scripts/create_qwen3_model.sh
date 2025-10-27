#!/bin/bash
# Create A2IA Qwen 3 model (better tool calling than Qwen 2.5)

set -e

echo "======================================================================"
echo "  Creating A2IA Qwen 3 Model (14B - Better Tool Calling)"
echo "======================================================================"
echo ""

# Check if base model exists
if ! ollama list | grep -q "qwen3:14b"; then
    echo "Base model not found. Pulling qwen3:14b..."
    echo "⚠️  Warning: This is 9.3GB and will take a few minutes..."
    ollama pull qwen3:14b
    echo ""
fi

echo "Creating a2ia-qwen3 from Modelfile-qwen3..."
ollama create a2ia-qwen3 -f Modelfile-qwen3

echo ""
echo "======================================================================"
echo "✅ Model created successfully!"
echo "======================================================================"
echo ""
echo "Qwen 3 Advantages:"
echo "  - Better tool calling consistency"
echo "  - Larger model (14B vs 7B) = better reasoning"
echo "  - Less likely to output JSON text instead of tool calls"
echo ""
echo "Usage:"
echo ""
echo "  # Test the model"
echo "  ollama run a2ia-qwen3"
echo ""
echo "  # Use with A2IA CLI"
echo "  a2ia-cli --model a2ia-qwen3"
echo ""
echo "======================================================================"
echo ""
echo "Model details:"
ollama show a2ia-qwen3
echo ""

