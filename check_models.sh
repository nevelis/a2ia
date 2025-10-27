#!/bin/bash
# Quick script to check available models

echo "Available Ollama models:"
echo "======================="
ollama list

echo ""
echo "Checking capybara models specifically:"
echo "======================================="
ollama list | grep capybara || echo "No capybara models found"

echo ""
echo "To create capybara-sdlc:"
echo "  cd /home/aaron/dev/nevelis/capybara"
echo "  ollama create capybara-sdlc -f Modelfile-capybara"

