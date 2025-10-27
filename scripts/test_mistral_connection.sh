#!/bin/bash
# Test a2ia-mistral connection from multiple angles

echo "======================================================================"
echo "  Testing a2ia-mistral Connection"
echo "======================================================================"
echo ""

echo "1. Checking Ollama is running..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "   ✅ Ollama server is running"
else
    echo "   ❌ Ollama server is NOT running"
    exit 1
fi
echo ""

echo "2. Checking model exists..."
if ollama list | grep -q "a2ia-mistral"; then
    echo "   ✅ a2ia-mistral model exists"
    ollama list | grep "a2ia-mistral"
else
    echo "   ❌ a2ia-mistral model NOT found"
    echo "   Run: ./create_mistral_model.sh"
    exit 1
fi
echo ""

echo "3. Testing direct Ollama communication..."
RESPONSE=$(timeout 15 ollama run a2ia-mistral "Reply with just: OK" 2>&1 | tail -5)
if echo "$RESPONSE" | grep -qi "ok"; then
    echo "   ✅ Direct Ollama communication works"
else
    echo "   ⚠️  Response: $RESPONSE"
fi
echo ""

echo "4. Testing A2IA OllamaClient..."
cd /home/aaron/dev/nevelis/a2ia
python3 -c "
import asyncio
from a2ia.client.llm import OllamaClient

async def test():
    client = OllamaClient(model='a2ia-mistral:latest')
    try:
        response = await client.chat([{'role': 'user', 'content': 'Reply: TEST'}], temperature=0.3)
        content = response.get('content', '')
        if content:
            print('   ✅ A2IA OllamaClient works')
            print(f'   Response: {content[:60]}...')
        else:
            print('   ❌ Empty response')
    except Exception as e:
        print(f'   ❌ Error: {e}')

asyncio.run(test())
" 2>&1
echo ""

echo "5. Checking MCP server..."
if pgrep -f "a2ia.server.*mcp" > /dev/null; then
    echo "   ✅ MCP server is running"
else
    echo "   ⚠️  MCP server is not running (will start with CLI)"
fi
echo ""

echo "======================================================================"
echo "All systems check complete!"
echo "======================================================================"
echo ""
echo "To use a2ia-mistral with A2IA CLI:"
echo ""
echo "  a2ia-cli --model a2ia-mistral"
echo ""
echo "Or with the :latest tag explicitly:"
echo ""
echo "  a2ia-cli --model a2ia-mistral:latest"
echo ""

