#!/bin/bash
# Create custom Capybara SDLC model

set -e

echo "======================================================================"
echo "  Creating Capybara SDLC Model"
echo "======================================================================"
echo ""

# Check if the merged model directory exists
if [ ! -d "./outputs/llama31-8b-sdlc-merged" ]; then
    echo "❌ Error: Merged model not found at ./outputs/llama31-8b-sdlc-merged"
    echo ""
    echo "Please ensure you have:"
    echo "  1. Trained your LoRA adapter"
    echo "  2. Merged it with: python -m src.merge_adapter"
    echo ""
    exit 1
fi

echo "Creating capybara-sdlc from Modelfile-capybara..."
ollama create capybara-sdlc -f Modelfile-capybara

echo ""
echo "======================================================================"
echo "✅ Model created successfully!"
echo "======================================================================"
echo ""
echo "Capybara SDLC Features:"
echo "  - Based on Llama 3.1 8B Instruct"
echo "  - Trained on SDLC lifecycle tasks"
echo "  - Contamination-resistant (tool outputs = evidence only)"
echo "  - Supports: sprint planning, architecture review, effort estimation"
echo ""
echo "Usage:"
echo ""
echo "  # Test the model"
echo "  ollama run capybara-sdlc"
echo ""
echo "  # Use with A2IA CLI (now the default!)"
echo "  a2ia-cli"
echo ""
echo "  # Or explicitly specify"
echo "  a2ia-cli --model capybara-sdlc:latest"
echo ""
echo "======================================================================"
echo ""
echo "Model details:"
ollama show capybara-sdlc
echo ""

