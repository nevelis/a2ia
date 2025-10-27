# CLI Streaming & Model Improvements

## Date: October 27, 2025

## Summary

Successfully implemented streaming responses in the A2IA CLI and fixed critical issues with tool calling by improving the Modelfile prompt and tool schema presentation.

---

## Changes Made

### 1. **Streaming Implementation** ✨

#### Added to `a2ia/client/llm.py`:
- New `stream_chat()` method that yields response chunks as they arrive from Ollama
- Uses `httpx.AsyncClient.stream()` for real-time streaming
- Properly handles JSON streaming format from Ollama API

#### Added to `a2ia/client/orchestrator.py`:
- New `process_turn_streaming()` method for streaming orchestration
- Yields structured chunks with types:
  - `'content'`: Text chunks as they arrive
  - `'tool_call'`: Tool invocation with name and args
  - `'tool_result'`: Tool execution results
  - `'tool_error'`: Tool errors
  - `'done'`: Final completion
- Accumulates streaming content while executing tools

#### Updated `a2ia/cli/interface.py`:
- Replaced blocking `process_turn()` with streaming version
- Real-time text display with `flush=True`
- Immediate tool call and result visualization
- **Result: No more waiting!** Text appears as the model generates it

### 2. **Tool Schema Improvements** 🔧

#### Problem Identified:
The LLM was:
- Hallucinating tool names (e.g., `container.exec`)
- Using wrong parameter names (e.g., `ignore_case` for `Grep`, `line_end` for `ReadFile`)
- Getting stuck in tool call loops

#### Root Cause:
The Modelfile template only showed tool names and descriptions, not parameter schemas!

```template
# OLD (broken)
* **{{ .Function.Name }}**: {{ .Function.Description }}

# NEW (fixed)
### {{ .Function.Name }}
{{ .Function.Description }}

Parameters:
- **{{ $key }}** ({{ $value.Type }} - required): {{ $value.Description }}
```

#### Updated `Modelfile`:
1. **Removed ExecuteTurk references** - ChatGPT-only workaround that confused the model
2. **Added detailed tool schema rendering** - Shows exact parameter names, types, and requirements
3. **Added explicit warning** - "IMPORTANT: Only use the tools listed above. Do not invent tool names or parameters."
4. **Cleaned up system prompt** - Removed references to TurkList and other deprecated concepts
5. **Simplified workspace guidance** - Clear instructions to use "/" as workspace root

#### Updated `Modelfile-gpt-oss`:
- Removed TurkInfo reference
- Kept consistent with main Modelfile philosophy

### 3. **Model Rebuilding**
Rebuilt both models with updated Modelfiles:
- `a2ia-qwen` (llama3.1:8b)
- `a2ia-gpt-oss` (gpt-oss:20b)

---

## Testing

### Streaming Tests ✅
Created and ran comprehensive tests:
1. **Basic streaming**: Text appears immediately character-by-character
2. **Tool call streaming**: Content → Tool call → Tool result → More content
3. **Error handling**: Proper error display and recovery

All tests passed successfully!

---

## User Experience Improvements

### Before:
```
User: What files are here?
[... 5-10 second wait ...]
A2IA: [entire response dumps at once]
```

### After:
```
User: What files are here?
A2IA: Let me check the 
🔧 ListDirectory({})
   ↳ success: True, files: [...]
directory. The files are:
- file1.txt
- file2.txt
...
```

**Feels responsive and interactive!** 🎉

---

## Technical Details

### Streaming Flow:
1. User sends message
2. Orchestrator streams LLM response
3. Text chunks printed immediately with `flush=True`
4. Tool calls accumulated during stream
5. After stream completes, tools execute
6. Tool results shown immediately
7. Next iteration streams response to tool results

### Why Tool Calls Aren't Streamed:
Ollama's current behavior:
- **Text content**: Streams in real-time ✨
- **Tool calls**: Sent at end of response (batched)

This is actually fine because:
1. LLM thinks/explains first (streamed)
2. Then decides which tools to call (sent together)
3. Tools execute with immediate feedback
4. Response to results is streamed

The user sees the reasoning process immediately!

---

## Files Modified

- `a2ia/client/llm.py` - Added `stream_chat()` method
- `a2ia/client/orchestrator.py` - Added `process_turn_streaming()` method
- `a2ia/cli/interface.py` - Updated to use streaming
- `Modelfile` - Major improvements to tool schema and prompt
- `Modelfile-gpt-oss` - Cleaned up deprecated references

---

## Next Steps

1. **Test with real workflows** - Try the CLI with actual tasks
2. **Monitor tool calling accuracy** - Verify the improved schema fixes hallucinations
3. **Consider adding streaming to REST API** - If needed for web interface
4. **Optimize context window** - Template is longer now, monitor token usage

---

## Notes

### Tool Parameter Schema Format
The template now extracts full parameter details from MCP tool definitions:
- Parameter name (exact spelling required)
- Parameter type (string, number, boolean, etc.)
- Required vs optional
- Description

This should eliminate the hallucination problem where LLMs invent parameter names based on their training data instead of using the actual available parameters.

### Streaming Protocol
Ollama streaming uses newline-delimited JSON:
```json
{"message": {"content": "chunk1"}}
{"message": {"content": "chunk2"}}
{"message": {"tool_calls": [...]}, "done": true}
```

We accumulate chunks and yield them for immediate display.

---

## Success Metrics

- ✅ Streaming works for text responses
- ✅ Streaming works with tool calls
- ✅ No linter errors
- ✅ Models rebuilt successfully
- ✅ ExecuteTurk references removed
- ✅ Tool schema properly displayed
- 🎯 Awaiting user testing for tool calling accuracy

---

## Potential Issues to Watch

1. **Template token usage** - The detailed tool schema adds tokens to every request
2. **Tool hallucinations** - Monitor if they're completely eliminated
3. **Streaming edge cases** - Network interruptions, incomplete chunks
4. **Performance** - Ensure streaming doesn't add latency

---

## Commands to Test

```bash
# Start the CLI
a2ia-cli

# Or with specific model
a2ia-cli --model a2ia-gpt-oss

# Test streaming with various prompts
You: Count from 1 to 100
You: What files are in this directory?
You: Write me a Python function to calculate fibonacci numbers
```

Watch for:
- Immediate text appearance
- Correct tool names and parameters
- No hallucinated tools like `container.exec`
- Smooth, responsive feel

