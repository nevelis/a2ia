#!/bin/bash
# Pull models for A2IA testing

echo "Pulling qwen2.5:7b..."
ollama pull qwen2.5:7b

echo "Pulling gemma3:4b..."
ollama pull gemma3:4b

echo "Pulling gemma3:12b..."
ollama pull gemma3:12b

echo "All models pulled!"
ollama list
