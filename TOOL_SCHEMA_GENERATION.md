# Tool Schema Generation

## Quick Start

Generate the complete tool schema documentation:

```bash
cd /home/aaron/dev/nevelis/a2ia
python3 scripts/generate_tool_schema.py
```

This creates three files:
- `tools.json` - Exact schema Ollama templates receive
- `tools_markdown.md` - Human-readable documentation
- `template_example.txt` - Template integration examples

## Why This Matters

### The Template Receives Structured Data

When A2IA calls Ollama with tools, it passes a JSON array via the API.
Ollama then makes this available to your Modelfile template as `$.Tools`.

The template needs to format this data appropriately for the model.

### The $value.Required Bug

We discovered that `{{- if $value.Required }}` doesn't work because:

**Tool Schema Structure:**
```json
{
  "function": {
    "parameters": {
      "properties": {
        "path": {
          "type": "string",
          "description": "File path"
          // NO "required" field here!
        }
      },
      "required": ["path"]  // Required fields are in a separate array
    }
  }
}
```

Properties have `.Type` and `.Description`, but **not** `.Required`.
Required fields are in a separate `parameters.required` array.

### Solution

Don't try to access `$value.Required` - just show all parameters:

```
{{- range $key, $value := .Function.Parameters.Properties }}
- **{{ $key }}** ({{ $value.Type }}): {{ $value.Description }}
{{- end }}
```

## Understanding the Schema

### Ollama Format

A2IA converts MCP tools to OpenAI/Ollama format:

```json
{
  "type": "function",
  "function": {
    "name": "tool_name",
    "description": "What the tool does",
    "parameters": {
      "type": "object",
      "properties": {
        "param1": {
          "type": "string",
          "description": "Parameter description"
        }
      },
      "required": ["param1"]
    }
  }
}
```

### Template Access

In your Modelfile template:

```
{{- range $.Tools }}
  Name: {{ .Function.Name }}
  Description: {{ .Function.Description }}
  
  {{- range $key, $value := .Function.Parameters.Properties }}
    Param: {{ $key }}
    Type: {{ $value.Type }}
    Description: {{ $value.Description }}
  {{- end }}
{{- end }}
```

## Files Generated

### tools.json

**Purpose:** Exact schema for integration and debugging

**Use for:**
- Verifying what templates receive
- Sharing with other systems
- API documentation
- Template development

### tools_markdown.md

**Purpose:** Human-readable documentation

**Contains:**
- Formatted tool descriptions
- Parameter tables
- JSON schema details (expandable)

**Use for:**
- Team documentation
- Model fine-tuning data
- Understanding available tools

### template_example.txt

**Purpose:** Template development guide

**Contains:**
- Example tool data
- Template iteration patterns
- Available fields reference
- Common pitfalls (like .Required)

**Use for:**
- Writing new templates
- Debugging template issues
- Understanding data structure

## Regenerating

Run the generator whenever:

1. **Tools Added/Removed**
   ```bash
   # After modifying a2ia/tools/*.py
   python3 scripts/generate_tool_schema.py
   ```

2. **Parameter Changes**
   ```bash
   # After changing tool schemas
   python3 scripts/generate_tool_schema.py
   ```

3. **Documentation Updates**
   ```bash
   # To refresh docs
   python3 scripts/generate_tool_schema.py
   ```

## Integration with Capybara Models

Your Capybara models use the fixed template that correctly handles this schema:

```
# In Modelfile-capybara and Modelfile-gguf
TEMPLATE """
{{- if $.Tools }}
## Available Tools
{{- range $.Tools }}
### {{ .Function.Name }}
{{ .Function.Description }}

Parameters:
{{- range $key, $value := .Function.Parameters.Properties }}
- **{{ $key }}** ({{ $value.Type }}): {{ $value.Description }}
{{- end }}
{{- end }}
{{- end }}
"""
```

Notice: No `{{- if $value.Required }}` - that was the bug!

## Example Tools

Your A2IA installation includes tools like:

- **File Operations**: `read_file`, `write_file`, `patch_file`, `list_directory`
- **Git**: `git_status`, `git_commit`, `git_diff`, `git_log`
- **Execution**: `execute_command`, `run_python`
- **Memory**: `store_memory`, `recall_memory`, `search_memory`
- **Search**: `grep_search`, `semantic_search`

Run the generator to see the complete list with all parameters!

## Debugging Templates

If your template fails:

1. Generate `tools.json`
2. Check what fields actually exist
3. Verify your template uses only available fields
4. Test iteration logic with sample data

The `template_example.txt` file shows exactly what fields are available.

