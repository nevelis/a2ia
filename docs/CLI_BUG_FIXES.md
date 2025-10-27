# CLI Bug Fixes

## Date: October 27, 2025

## Issues Fixed

### 1. **Label Splitting Issue** ✅

**Problem:**
The "A2IA:" label was being printed on EVERY content chunk after a tool call, causing words to be split:
```
A2IA: I
A2IA: 've pulled the latest...
```

**Root Cause:**
The `after_tool` flag was being set to False in the middle of the content handling logic, but the elif condition would trigger on every chunk while it was still True.

**Fix:**
Ensured `after_tool = False` is set immediately after printing the label, so subsequent chunks don't trigger the elif condition.

**Code Change:**
```python
elif after_tool:
    # Re-print A2IA label after tool output (only once)
    print(f"\n\033[36mA2IA:\033[0m ", end='', flush=True)
    after_tool = False  # Clear flag immediately so we don't print again
```

**Result:**
Now correctly prints:
```
A2IA: I've pulled the latest...
```

---

### 2. **Missing `ignore_case` Parameter in `grep` Tool** ✅

**Problem:**
The LLM was trying to use `grep(ignore_case=True, ...)` but the tool didn't support that parameter:
```
🔧 Grep(ignore_case=True, path='./', pattern='ghost doctrine', recursive=True, regex=False)
   ✗ grep() got an unexpected keyword argument 'ignore_case'
```

**Root Cause:**
The REST API definition included `ignore_case` parameter but the actual MCP tool didn't implement it.

**Fix:**
Added `ignore_case` parameter to the `grep` tool with proper implementation:
- For simple string matching: Convert both pattern and line to lowercase
- For regex matching: Add `re.IGNORECASE` flag

**Code Changes:**
```python
async def grep(pattern: str, path: str, regex: bool = False, recursive: bool = False, ignore_case: bool = False) -> dict:
    """Search for pattern in file(s).
    
    Args:
        pattern: Search pattern
        path: File or directory path
        regex: Use regex pattern matching (default: False)
        recursive: Search recursively in directories (default: False)
        ignore_case: Case-insensitive search (default: False)  # NEW!
```

Implementation:
- If `ignore_case=True` and `regex=False`: Use `.lower()` on both pattern and line
- If `ignore_case=True` and `regex=True`: Pass `re.IGNORECASE` flag

**Result:**
The tool now works with case-insensitive searches as the LLM expects.

---

### 3. **Context Investigation - Added Debug Mode** 🔍

**Issue Reported:**
User asked to recall memory, LLM said it did, but then when asked to summarize, it started looking through files instead of using the recalled memory.

**Investigation:**
Added `--debug` flag to CLI to show message history and verify tool results are being properly added.

**Code Changes:**
```python
# CLI now accepts --debug flag
cli = CLI(model="a2ia-qwen", debug=True)

# Shows last 5 messages after each turn
if self.debug:
    print("\n" + "="*70)
    print("DEBUG: Message History")
    print("="*70)
    messages = self.orchestrator.get_messages()
    for i, msg in enumerate(messages[-5:]):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        # Truncate long content for display
        if len(content) > 200:
            content = content[:200] + "..."
        print(f"{i+1}. [{role}]: {content}")
    print("="*70 + "\n")
```

**Usage:**
```bash
a2ia-cli --debug
```

**Verification:**
Tool results ARE being added to message history with full content:
```python
# Line 345 in orchestrator.py
result_json = json.dumps(result) if isinstance(result, dict) else str(result)
self.messages.append({
    'role': 'user',
    'content': f'[Tool result from {tool_name}]: {result_json}'
})
```

So the full memory content IS sent to the LLM, even though the display shows a truncated version.

**Possible Root Causes of Behavior:**
1. **Model confusion:** The LLM might not understand it should use the recalled memory
2. **Context window:** If there are many messages, earlier tool results might be getting truncated
3. **Prompt clarity:** The prompt might need to be clearer about using tool results

**Next Steps:**
- Use `--debug` mode to verify full context is being sent
- If context IS complete, this is a model behavior issue, not a code issue
- May need to improve the prompt or use a different model

---

## Files Modified

1. **`a2ia/cli/interface.py`**
   - Fixed label splitting by ensuring `after_tool = False` is set immediately
   - Added `--debug` flag support
   - Added debug output showing message history

2. **`a2ia/tools/filesystem_tools.py`**
   - Added `ignore_case` parameter to `grep` tool
   - Implemented case-insensitive search for both string and regex modes

---

## Testing

### Test Label Fix:
```bash
a2ia-cli
You: What files are here?
# Watch for clean "A2IA: The files..." without splitting
```

### Test grep Fix:
```bash
a2ia-cli
You: Search for "ghost doctrine" in all files
# Should work without errors
```

### Test Debug Mode:
```bash
a2ia-cli --debug
You: Recall memories about streaming
# After response, see full message history
```

---

## Summary

✅ **Label splitting fixed** - Words no longer split with duplicate "A2IA:" labels  
✅ **grep tool fixed** - Now supports `ignore_case` parameter  
✅ **Debug mode added** - Can verify message history is complete  
⚠️ **Context investigation** - Tool results ARE being added, may be model behavior issue  

---

## Additional Notes

### Display vs. Context
It's important to understand the distinction:
- **Display (user sees):** Truncated to 150 chars for readability
- **Context (LLM receives):** Full JSON result with all data

When you see:
```
↳ memories: [{'memory_id': 'mem_...', 'content': 'The Ghost Doctrine 👻 — "Today's warnings are the ghosts o...
```

The LLM is receiving:
```
[Tool result from recall_memory]: {"query": "ghost doctrine", "memories": [{"memory_id": "mem_20251023_140347_903003", "content": "The Ghost Doctrine 👻 — 'Today's warnings are the ghosts of tomorrow's bugs...' [FULL CONTENT HERE]", ...}], ...}
```

### Debugging Workflow

1. **Enable debug mode:**
   ```bash
   a2ia-cli --debug
   ```

2. **After each interaction, check the message history output**

3. **Verify tool results are complete:**
   - Look for `[Tool result from X]: {full json}`
   - Check that memory content, file content, etc. is included

4. **If context is complete but behavior is wrong:**
   - This is a model issue, not a code issue
   - Try a different model: `--model a2ia-gpt-oss`
   - Or improve the system prompt

---

## Future Improvements

### Potential Enhancements:
1. **Smart truncation** - Truncate less important fields, keep key content
2. **Context compression** - Summarize old tool results to save tokens
3. **Explicit prompting** - Add "Use the tool results above" to system messages
4. **Model tuning** - Fine-tune on examples of using tool results properly

### Grep Enhancements:
1. **Line number ranges** - Only show lines X-Y
2. **Max matches** - Limit number of results
3. **File type filtering** - Only search .py, .md, etc.
4. **Exclude patterns** - Ignore certain files/directories

