#!/bin/bash
# Quick vLLM health check script

echo "Checking vLLM status..."
echo ""

# Check if vLLM is installed
if python3 -c "import vllm" 2>/dev/null; then
    VERSION=$(python3 -c "import vllm; print(vllm.__version__)")
    echo "✅ vLLM installed (version: $VERSION)"
else
    echo "❌ vLLM not installed"
    echo ""
    echo "To install: ./vllm_setup.sh"
    exit 1
fi

# Check if vLLM server is running
echo ""
echo "Checking vLLM server..."
if curl -s -f http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ vLLM server is running on http://localhost:8000"
    echo ""
    echo "Server info:"
    curl -s http://localhost:8000/v1/models 2>/dev/null | python3 -m json.tool
else
    echo "❌ vLLM server is NOT running"
    echo ""
    echo "To start: ./vllm_start.sh"
    exit 1
fi

echo ""
echo "✅ Everything looks good!"

