# Known Issues & Limitations

## Context Contamination with Memory Tools

### Issue

When using `RecallMemory` or `ListMemories`, the LLM may treat memory **content** as current **instructions**.

**Example:**
```
User: What is the Ghost Doctrine?

🔍 RecallMemory(query='Ghost Doctrine')
   ↳ memories: [{content: "Ghost Doctrine + Action Plan..."}]

A2IA: [Outputs the entire action plan from memory instead of summarizing]
```

### Root Cause

Current models (llama3.1:8b, gpt-oss:20b) don't naturally distinguish between:
- **Data to reason about** (memory content)
- **Instructions to execute** (action plans within that content)

### Why This Happens

LLMs are trained to continue patterns. When they see:
```
Step 1: Do X
Step 2: Do Y
```

They naturally continue with "Step 3" or execute the steps, even if that text came from a memory retrieval.

### Solutions

#### Option 1: Use a Larger/Better Model ✅ RECOMMENDED
```bash
# Models that better separate data from instructions:
ollama pull mixtral:8x22b
a2ia-cli --model mixtral:8x22b

# Or use with ReAct mode:
a2ia-cli --model mixtral:8x22b --react
```

**Pro:** Actually solves the problem  
**Con:** Requires more VRAM/compute

#### Option 2: Use ReAct Mode (Experimental) ⚠️
```bash
a2ia-cli --react
```

Requires model fine-tuning or a model that naturally follows structured formats.

**Pro:** Visible reasoning, better control  
**Con:** Current models don't follow the format without fine-tuning

#### Option 3: Store Only Principles (Workaround)
Don't store action plans in memory - only store definitions and principles.

**Example - Bad:**
```
Memory: "Ghost Doctrine: Warnings are ghosts...
Action Plan:
Step 1: Review code
Step 2: Fix warnings
...
```

**Example - Good:**
```
Memory: "Ghost Doctrine: 'Warnings are the ghosts of future failures' - a principle emphasizing the importance of addressing all warnings during development."
```

**Pro:** Works with current setup  
**Con:** Limits what you can store

### What Was Tried (and Didn't Work)

1. ❌ **Safety Wrappers** - Adding "[INFORMATION ONLY]" prefixes
   - Models ignore them
   
2. ❌ **Content Sanitization** - Removing action plans from memory results
   - Too brittle, hard to maintain, misses edge cases
   
3. ❌ **System Prompts** - Explicit instructions not to follow memory content
   - Models don't reliably follow these meta-instructions

### When This Is NOT a Problem

This issue doesn't affect:
- ✅ File reading (code is clearly data)
- ✅ Git operations (output is clearly informational)
- ✅ Directory listings (clearly data)
- ✅ Simple Q&A without tool use

It ONLY affects:
- ❌ Memory retrieval with action plans
- ❌ Memory retrieval with task lists
- ❌ Memory retrieval with instructional content

### Recommendation

For now, with current models:
1. **Be selective** about what you store in memory
2. **Store principles, not plans**
3. **Consider upgrading** to a larger model if this is critical
4. **Wait for better local models** that handle this better

This is a **model capability issue**, not a code bug. The proper fix requires either:
- Model fine-tuning
- Using larger/better models
- Fundamental architecture changes (classifier-based tool calling)

---

## Other Known Issues

### Streaming with Native Tool Calling

**Issue:** Ollama streams text but sends tool calls at the end (not streamed).

**Impact:** Can't show thinking before tool calls without ReAct format.

**Status:** Limitation of Ollama's streaming implementation.

---

## What Works Well ✅

- Streaming responses (text content)
- Tool validation & throttling
- Tool-specific emojis
- Error handling
- Rate limiting
- Debug mode
- Multiple model support

