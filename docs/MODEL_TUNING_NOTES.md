# Model Tuning Notes

## Issue: Qwen Outputting JSON Text Instead of Tool Calls

**Date:** 2025-10-27  
**Problem:** a2ia-qwen sometimes outputs JSON text like `{"name": "tool", "arguments": {...}}` instead of using the proper tool calling mechanism.

### Root Cause

The model gets confused mid-conversation when it sees tool results formatted as JSON. It starts mimicking the JSON format instead of using the tool calling interface.

### Fixes Applied

1. **Stronger Instructions:**
   ```
   CRITICAL: When tools are available, you MUST use them by calling them directly.
   - NEVER output tool calls as JSON text
   - If you need to call a tool, DO IT - don't describe the call in text
   ```

2. **Lower Temperature:**
   - Changed from `0.3` to `0.2` for more deterministic behavior
   - Increased `repeat_penalty` from `1.05` to `1.1`

3. **Model Behavior:**
   - When tested in isolation: ✅ Works correctly
   - In conversation: ⚠️ Can degenerate to JSON text
   - Fix: Stronger system prompt instructions + lower temp

### Testing

```bash
# Test tool calling
python3 << 'EOF'
import asyncio
from a2ia.client.llm import OllamaClient

async def test():
    client = OllamaClient(model='a2ia-qwen')
    tools = [{
        'type': 'function',
        'function': {
            'name': 'test_tool',
            'description': 'Test',
            'parameters': {'type': 'object', 'properties': {}}
        }
    }]
    
    response = await client.chat(
        [{'role': 'user', 'content': 'Use the test tool'}],
        tools=tools,
        temperature=0.2
    )
    
    if 'tool_calls' in response:
        print("✅ Proper tool calls")
    else:
        print("❌ No tool calls, content:", response.get('content', '')[:100])

asyncio.run(test())
EOF
```

### Alternative: Mistral with ReAct

If Qwen continues to have issues, use Mistral with ReAct mode:

```bash
a2ia-cli --model a2ia-mistral --react
```

ReAct mode uses text-based tool calling which doesn't have this confusion issue.

### Parameters Comparison

| Parameter | Old Value | New Value | Reason |
|-----------|-----------|-----------|--------|
| temperature | 0.3 | 0.2 | More deterministic tool calling |
| repeat_penalty | 1.05 | 1.1 | Prevent JSON pattern repetition |

### When This Occurs

- ✅ First tool call: Usually works
- ⚠️ After tool results: Model sees JSON and mimics it
- ❌ Multiple rounds: Gets worse over time

### Mitigation Strategies

1. **System Prompt:** Emphasize "NEVER output JSON text"
2. **Temperature:** Lower to 0.1-0.2 for tool-heavy tasks
3. **ReAct Mode:** Use --react as fallback
4. **Context Management:** Clear history if model starts degrading

### Model Comparison

| Model | Tool Calling | JSON Text Issue | Recommended |
|-------|--------------|-----------------|-------------|
| a2ia-qwen | Native ✅ | Sometimes ⚠️ | Yes (with low temp) |
| a2ia-mistral | ReAct only | No ✅ | Backup |
| a2ia-llama3 | Native ✅ | Rare ⚠️ | Alternative |

---

**Status:** Tuned and improved  
**Next:** Monitor behavior in multi-turn conversations

