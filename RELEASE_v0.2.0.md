# A2IA v0.2.0 Release Notes

## 🚀 Deployed to Production

**Server:** a2ia.amazingland.live
**Status:** Code synced, ready to restart

## What's New

### 🛠️ 14 New Tools (39 Total!)

**File Utilities (3):**
- Head - Read first N lines
- Tail - Read last N lines
- Grep - Search with regex/ripgrep support

**Enhanced File Operations (2):**
- FindReplace - Better than edit_file
- FindReplaceRegex - Regex search & replace

**Terraform Integration (11):**
- TerraformInit, TerraformPlan, TerraformApply
- TerraformDestroy, TerraformValidate
- TerraformWorkspace, TerraformImport
- TerraformState, TerraformTaint, TerraformUntaint
- TerraformOutput

### ✨ CLI Improvements

**New CLI Tool:** `a2ia-cli`
- Interactive chat with Ollama models
- 39 tools with TitleCase names
- Clean output: `🔧 ToolName(args)`
- Path sanitization (workspace → /)
- 300 max iterations
- Model: a2ia-llama3 (llama3.1:8b with tool support)

### 🎯 ChatGPT/REST API Improvements

**Enhanced Endpoints:**
- GET /workspace/files/{path}/head
- GET /workspace/files/{path}/tail
- POST /workspace/grep
- POST /terraform/* (init, plan, apply, validate)

**All Tools:**
- TitleCase operation IDs
- Detailed OpenAPI descriptions
- x-openai-isConsequential: false
- Path sanitization

### 🧪 Test Coverage

**136 tests passing** (up from 125):
- 106 original A2IA tests
- 6 new filesystem tool tests
- 6 file utility tests (Head/Tail/Grep)
- 5 Terraform tests
- 7 LLM client tests
- 4 orchestrator tests
- 2 MCP client unit tests

### 📝 Prompt Improvements

**More Directive Behavior:**
- "TOOL FIRST" - use tools immediately
- "NO EXPLANATIONS BEFORE ACTING"
- "KEEP USING TOOLS" - chain them
- Dynamic tool injection via template
- Clear workspace context ("/" = root)

## 🔄 To Restart

### On amazingland.live:

```bash
ssh aaron@amazingland.live
cd ~/a2ia
.venv/bin/python -m a2ia.server --mode http --host 127.0.0.1 --port 8000
```

### Local CLI:

```bash
a2ia-cli --model a2ia-llama3
```

## 📊 Summary

**Total Tools:** 39 (was 26)
**Total Tests:** 136 passing (was 125)
**New Features:**
- Complete CLI with Ollama
- Terraform automation
- Better file utilities (Head/Tail/Grep)
- Enhanced find/replace tools
- TitleCase names everywhere

**Production Ready:** ✅
- All tests passing
- REST API updated
- CLI functional
- Code deployed

## 🎁 What ChatGPT Gets

ChatGPT Actions now have access to:
- 39 tools with clean TitleCase names
- Better file editing (FindReplace, FindReplaceRegex, PatchFile)
- File inspection (Head, Tail, Grep)
- Full Terraform automation
- No path leakage (workspace sanitized to /)

---

**Ready to restart the server!** 🚀
