#!/bin/bash
# Simple test to compare both models

echo "========================================="
echo "Testing capybara-sdlc (working)"
echo "========================================="
curl -s http://localhost:11434/api/chat \
  -d '{"model": "capybara-sdlc:latest", "messages": [{"role": "user", "content": "Say hi"}], "stream": false}' \
  | python3 -m json.tool

echo ""
echo ""
echo "========================================="
echo "Testing capybara-gguf (failing?)"
echo "========================================="
curl -s http://localhost:11434/api/chat \
  -d '{"model": "capybara-gguf:latest", "messages": [{"role": "user", "content": "Say hi"}], "stream": false}' \
  | python3 -m json.tool

echo ""
echo ""
echo "========================================="
echo "Comparing templates"
echo "========================================="
echo "capybara-sdlc template:"
curl -s http://localhost:11434/api/show -d '{"name": "capybara-sdlc:latest"}' \
  | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('template', 'N/A')[:200])"

echo ""
echo "capybara-gguf template:"
curl -s http://localhost:11434/api/show -d '{"name": "capybara-gguf:latest"}' \
  | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('template', 'N/A')[:200])"

