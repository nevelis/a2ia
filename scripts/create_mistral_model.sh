#!/bin/bash
# Create custom A2IA Mistral model

set -e

echo "======================================================================"
echo "  Creating A2IA Mistral Model"
echo "======================================================================"
echo ""

# Check if base model exists
if ! ollama list | grep -q "mistral:7b-instruct-q4_K_M"; then
    echo "Base model not found. Pulling mistral:7b-instruct-q4_K_M..."
    ollama pull mistral:7b-instruct-q4_K_M
    echo ""
fi

echo "Creating a2ia-mistral from Modelfile-mistral..."
ollama create a2ia-mistral -f Modelfile-mistral

echo ""
echo "======================================================================"
echo "✅ Model created successfully!"
echo "======================================================================"
echo ""
echo "Usage:"
echo ""
echo "  # Test the model"
echo "  ollama run a2ia-mistral"
echo ""
echo "  # Use with A2IA CLI"
echo "  a2ia-cli --model a2ia-mistral"
echo ""
echo "  # Use with A2IA CLI and show thinking"
echo "  a2ia-cli --model a2ia-mistral --show-thinking"
echo ""
echo "======================================================================"
echo ""
echo "Model details:"
ollama show a2ia-mistral
echo ""

