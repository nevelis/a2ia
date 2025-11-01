# A2IA Tool Schema Documentation

Generated automatically from MCP server.

**Total Tools:** 54

---

## 1. CreateWorkspace

**Description:** Get information about the persistent workspace.

NOTE: This tool is kept for backward compatibility. A2IA now uses a single
persistent workspace that is automatically initialized. Arguments are ignored.

Args:
    workspace_id: Ignored (kept for compatibility)
    base_path: Ignored (kept for compatibility)
    description: Ignored (kept for compatibility)

Returns:
    Dictionary with workspace information


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workspace_id` | unknown |  |  |
| `base_path` | unknown |  |  |
| `description` | unknown |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "CreateWorkspace",
    "description": "Get information about the persistent workspace.\n\nNOTE: This tool is kept for backward compatibility. A2IA now uses a single\npersistent workspace that is automatically initialized. Arguments are ignored.\n\nArgs:\n    workspace_id: Ignored (kept for compatibility)\n    base_path: Ignored (kept for compatibility)\n    description: Ignored (kept for compatibility)\n\nReturns:\n    Dictionary with workspace information\n",
    "parameters": {
      "type": "object",
      "properties": {
        "workspace_id": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Workspace Id"
        },
        "base_path": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Base Path"
        },
        "description": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Description"
        }
      },
      "required": []
    }
  }
}
```

</details>

---

## 2. GetWorkspaceInfo

**Description:** Get information about the current workspace.

Returns:
    Dictionary with workspace details


**Parameters:** None

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GetWorkspaceInfo",
    "description": "Get information about the current workspace.\n\nReturns:\n    Dictionary with workspace details\n",
    "parameters": {
      "type": "object",
      "properties": {},
      "required": []
    }
  }
}
```

</details>

---

## 3. CloseWorkspace

**Description:** No-op: Workspace is persistent and cannot be closed.

NOTE: This tool is kept for backward compatibility. The workspace
remains active and persistent.

Returns:
    Dictionary with status message


**Parameters:** None

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "CloseWorkspace",
    "description": "No-op: Workspace is persistent and cannot be closed.\n\nNOTE: This tool is kept for backward compatibility. The workspace\nremains active and persistent.\n\nReturns:\n    Dictionary with status message\n",
    "parameters": {
      "type": "object",
      "properties": {},
      "required": []
    }
  }
}
```

</details>

---

## 4. PatchFile

**Description:** Apply a unified diff deterministically with context verification and EOF insertion alignment.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | ✓ |  |
| `diff` | string | ✓ |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "PatchFile",
    "description": "Apply a unified diff deterministically with context verification and EOF insertion alignment.",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "title": "Path",
          "type": "string"
        },
        "diff": {
          "title": "Diff",
          "type": "string"
        }
      },
      "required": [
        "path",
        "diff"
      ]
    }
  }
}
```

</details>

---

## 5. AppendFile

**Description:** 

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | ✓ |  |
| `content` | string | ✓ |  |
| `encoding` | string |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "AppendFile",
    "description": "",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "title": "Path",
          "type": "string"
        },
        "content": {
          "title": "Content",
          "type": "string"
        },
        "encoding": {
          "default": "utf-8",
          "title": "Encoding",
          "type": "string"
        }
      },
      "required": [
        "path",
        "content"
      ]
    }
  }
}
```

</details>

---

## 6. TruncateFile

**Description:** 

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | ✓ |  |
| `length` | integer |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "TruncateFile",
    "description": "",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "title": "Path",
          "type": "string"
        },
        "length": {
          "default": 0,
          "title": "Length",
          "type": "integer"
        }
      },
      "required": [
        "path"
      ]
    }
  }
}
```

</details>

---

## 7. PruneDirectory

**Description:** 

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | ✓ |  |
| `keep_patterns` | string |  |  |
| `dry_run` | boolean |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "PruneDirectory",
    "description": "",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "title": "Path",
          "type": "string"
        },
        "keep_patterns": {
          "default": null,
          "title": "keep_patterns",
          "type": "string"
        },
        "dry_run": {
          "default": false,
          "title": "Dry Run",
          "type": "boolean"
        }
      },
      "required": [
        "path"
      ]
    }
  }
}
```

</details>

---

## 8. ListDirectory

**Description:** List files in a directory.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string |  |  |
| `recursive` | boolean |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "ListDirectory",
    "description": "List files in a directory.",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "default": "",
          "title": "Path",
          "type": "string"
        },
        "recursive": {
          "default": false,
          "title": "Recursive",
          "type": "boolean"
        }
      },
      "required": []
    }
  }
}
```

</details>

---

## 9. ReadFile

**Description:** Read file content.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | ✓ |  |
| `encoding` | string |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "ReadFile",
    "description": "Read file content.",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "title": "Path",
          "type": "string"
        },
        "encoding": {
          "default": "utf-8",
          "title": "Encoding",
          "type": "string"
        }
      },
      "required": [
        "path"
      ]
    }
  }
}
```

</details>

---

## 10. WriteFile

**Description:** Write content to a file.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | ✓ |  |
| `content` | string | ✓ |  |
| `encoding` | string |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "WriteFile",
    "description": "Write content to a file.",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "title": "Path",
          "type": "string"
        },
        "content": {
          "title": "Content",
          "type": "string"
        },
        "encoding": {
          "default": "utf-8",
          "title": "Encoding",
          "type": "string"
        }
      },
      "required": [
        "path",
        "content"
      ]
    }
  }
}
```

</details>

---

## 11. DeleteFile

**Description:** Delete a file or directory.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | ✓ |  |
| `recursive` | boolean |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "DeleteFile",
    "description": "Delete a file or directory.",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "title": "Path",
          "type": "string"
        },
        "recursive": {
          "default": false,
          "title": "Recursive",
          "type": "boolean"
        }
      },
      "required": [
        "path"
      ]
    }
  }
}
```

</details>

---

## 12. MoveFile

**Description:** Move or rename a file.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `source` | string | ✓ |  |
| `destination` | string | ✓ |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "MoveFile",
    "description": "Move or rename a file.",
    "parameters": {
      "type": "object",
      "properties": {
        "source": {
          "title": "Source",
          "type": "string"
        },
        "destination": {
          "title": "Destination",
          "type": "string"
        }
      },
      "required": [
        "source",
        "destination"
      ]
    }
  }
}
```

</details>

---

## 13. FindReplace

**Description:** Find and replace text in a file.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | ✓ |  |
| `find_text` | string | ✓ |  |
| `replace_text` | string | ✓ |  |
| `encoding` | string |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "FindReplace",
    "description": "Find and replace text in a file.",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "title": "Path",
          "type": "string"
        },
        "find_text": {
          "title": "Find Text",
          "type": "string"
        },
        "replace_text": {
          "title": "Replace Text",
          "type": "string"
        },
        "encoding": {
          "default": "utf-8",
          "title": "Encoding",
          "type": "string"
        }
      },
      "required": [
        "path",
        "find_text",
        "replace_text"
      ]
    }
  }
}
```

</details>

---

## 14. FindReplaceRegex

**Description:** Find and replace using regex in a file.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | ✓ |  |
| `pattern` | string | ✓ |  |
| `replace_text` | string | ✓ |  |
| `encoding` | string |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "FindReplaceRegex",
    "description": "Find and replace using regex in a file.",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "title": "Path",
          "type": "string"
        },
        "pattern": {
          "title": "Pattern",
          "type": "string"
        },
        "replace_text": {
          "title": "Replace Text",
          "type": "string"
        },
        "encoding": {
          "default": "utf-8",
          "title": "Encoding",
          "type": "string"
        }
      },
      "required": [
        "path",
        "pattern",
        "replace_text"
      ]
    }
  }
}
```

</details>

---

## 15. Head

**Description:** Get the first N lines of a file.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | ✓ |  |
| `lines` | integer |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "Head",
    "description": "Get the first N lines of a file.",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "title": "Path",
          "type": "string"
        },
        "lines": {
          "default": 10,
          "title": "Lines",
          "type": "integer"
        }
      },
      "required": [
        "path"
      ]
    }
  }
}
```

</details>

---

## 16. Tail

**Description:** Get the last N lines of a file.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | ✓ |  |
| `lines` | integer |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "Tail",
    "description": "Get the last N lines of a file.",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "title": "Path",
          "type": "string"
        },
        "lines": {
          "default": 10,
          "title": "Lines",
          "type": "integer"
        }
      },
      "required": [
        "path"
      ]
    }
  }
}
```

</details>

---

## 17. Grep

**Description:** Search for pattern in file(s).

Args:
    pattern: Search pattern
    path: File or directory path
    regex: Use regex pattern matching (default: False)
    recursive: Search recursively in directories (default: False)
    ignore_case: Case-insensitive search (default: False)

Returns:
    Dictionary with search results


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `pattern` | string | ✓ |  |
| `path` | string | ✓ |  |
| `regex` | boolean |  |  |
| `recursive` | boolean |  |  |
| `ignore_case` | boolean |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "Grep",
    "description": "Search for pattern in file(s).\n\nArgs:\n    pattern: Search pattern\n    path: File or directory path\n    regex: Use regex pattern matching (default: False)\n    recursive: Search recursively in directories (default: False)\n    ignore_case: Case-insensitive search (default: False)\n\nReturns:\n    Dictionary with search results\n",
    "parameters": {
      "type": "object",
      "properties": {
        "pattern": {
          "title": "Pattern",
          "type": "string"
        },
        "path": {
          "title": "Path",
          "type": "string"
        },
        "regex": {
          "default": false,
          "title": "Regex",
          "type": "boolean"
        },
        "recursive": {
          "default": false,
          "title": "Recursive",
          "type": "boolean"
        },
        "ignore_case": {
          "default": false,
          "title": "Ignore Case",
          "type": "boolean"
        }
      },
      "required": [
        "pattern",
        "path"
      ]
    }
  }
}
```

</details>

---

## 18. ExecuteCommand

**Description:** Execute a shell command in the workspace.

Args:
    command: Shell command to execute
    timeout: Timeout in seconds (default: 30)
    cwd: Working directory relative to workspace (default: workspace root)
    env: Additional environment variables

Returns:
    Dictionary with stdout, stderr, returncode, and duration


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `command` | string | ✓ |  |
| `timeout` | integer |  |  |
| `cwd` | unknown |  |  |
| `env` | unknown |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "ExecuteCommand",
    "description": "Execute a shell command in the workspace.\n\nArgs:\n    command: Shell command to execute\n    timeout: Timeout in seconds (default: 30)\n    cwd: Working directory relative to workspace (default: workspace root)\n    env: Additional environment variables\n\nReturns:\n    Dictionary with stdout, stderr, returncode, and duration\n",
    "parameters": {
      "type": "object",
      "properties": {
        "command": {
          "title": "Command",
          "type": "string"
        },
        "timeout": {
          "default": 30,
          "title": "Timeout",
          "type": "integer"
        },
        "cwd": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Cwd"
        },
        "env": {
          "anyOf": [
            {
              "additionalProperties": {
                "type": "string"
              },
              "type": "object"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Env"
        }
      },
      "required": [
        "command"
      ]
    }
  }
}
```

</details>

---

## 19. ExecuteTurk

**Description:** Execute a shell command with human operator oversight.

Similar to execute_command, but with a human operator curating which
commands run and ensuring safe execution. Use this for complex or
sensitive operations where human judgment is valuable.

Tracks command usage for tooling gap analysis.

Args:
    command: Shell command to execute
    timeout: Timeout in seconds (default: 30)
    cwd: Working directory relative to workspace (default: workspace root)
    env: Additional environment variables

Returns:
    Dictionary with stdout, stderr, returncode, and duration


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `command` | string | ✓ |  |
| `timeout` | integer |  |  |
| `cwd` | unknown |  |  |
| `env` | unknown |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "ExecuteTurk",
    "description": "Execute a shell command with human operator oversight.\n\nSimilar to execute_command, but with a human operator curating which\ncommands run and ensuring safe execution. Use this for complex or\nsensitive operations where human judgment is valuable.\n\nTracks command usage for tooling gap analysis.\n\nArgs:\n    command: Shell command to execute\n    timeout: Timeout in seconds (default: 30)\n    cwd: Working directory relative to workspace (default: workspace root)\n    env: Additional environment variables\n\nReturns:\n    Dictionary with stdout, stderr, returncode, and duration\n",
    "parameters": {
      "type": "object",
      "properties": {
        "command": {
          "title": "Command",
          "type": "string"
        },
        "timeout": {
          "default": 300,
          "title": "Timeout",
          "type": "integer"
        },
        "cwd": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Cwd"
        },
        "env": {
          "anyOf": [
            {
              "additionalProperties": {
                "type": "string"
              },
              "type": "object"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Env"
        }
      },
      "required": [
        "command"
      ]
    }
  }
}
```

</details>

---

## 20. TurkInfo

**Description:** Get ExecuteTurk command usage statistics.

Shows which commands have been executed via ExecuteTurk and their frequency.
Used to identify tooling gaps that should be automated.

Returns:
    Dictionary with command usage statistics


**Parameters:** None

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "TurkInfo",
    "description": "Get ExecuteTurk command usage statistics.\n\nShows which commands have been executed via ExecuteTurk and their frequency.\nUsed to identify tooling gaps that should be automated.\n\nReturns:\n    Dictionary with command usage statistics\n",
    "parameters": {
      "type": "object",
      "properties": {},
      "required": []
    }
  }
}
```

</details>

---

## 21. TurkReset

**Description:** Reset ExecuteTurk command tracking.

Call this after reviewing turk_info and updating A2IA-Tooldev.md.

Returns:
    Dictionary with reset confirmation


**Parameters:** None

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "TurkReset",
    "description": "Reset ExecuteTurk command tracking.\n\nCall this after reviewing turk_info and updating A2IA-Tooldev.md.\n\nReturns:\n    Dictionary with reset confirmation\n",
    "parameters": {
      "type": "object",
      "properties": {},
      "required": []
    }
  }
}
```

</details>

---

## 22. StoreMemory

**Description:** Store knowledge in the semantic memory system.

Args:
    content: The knowledge content to store
    tags: Optional categorical tags for filtering
    metadata: Optional additional metadata

Returns:
    Dictionary with memory_id and stored_at timestamp


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `content` | string | ✓ |  |
| `tags` | unknown |  |  |
| `metadata` | unknown |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "StoreMemory",
    "description": "Store knowledge in the semantic memory system.\n\nArgs:\n    content: The knowledge content to store\n    tags: Optional categorical tags for filtering\n    metadata: Optional additional metadata\n\nReturns:\n    Dictionary with memory_id and stored_at timestamp\n",
    "parameters": {
      "type": "object",
      "properties": {
        "content": {
          "title": "Content",
          "type": "string"
        },
        "tags": {
          "anyOf": [
            {
              "items": {
                "type": "string"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Tags"
        },
        "metadata": {
          "anyOf": [
            {
              "additionalProperties": true,
              "type": "object"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Metadata"
        }
      },
      "required": [
        "content"
      ]
    }
  }
}
```

</details>

---

## 23. RecallMemory

**Description:** Recall memories using semantic search.

Args:
    query: The semantic search query
    limit: Maximum number of results to return (default: 5)
    tags: Optional tags to filter results (case-insensitive)

Returns:
    Dictionary with list of matching memories


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | ✓ |  |
| `limit` | integer |  |  |
| `tags` | unknown |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "RecallMemory",
    "description": "Recall memories using semantic search.\n\nArgs:\n    query: The semantic search query\n    limit: Maximum number of results to return (default: 5)\n    tags: Optional tags to filter results (case-insensitive)\n\nReturns:\n    Dictionary with list of matching memories\n",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "title": "Query",
          "type": "string"
        },
        "limit": {
          "default": 5,
          "title": "Limit",
          "type": "integer"
        },
        "tags": {
          "anyOf": [
            {
              "items": {
                "type": "string"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Tags"
        }
      },
      "required": [
        "query"
      ]
    }
  }
}
```

</details>

---

## 24. ListMemories

**Description:** List stored memories with optional filtering.

Args:
    limit: Maximum number of memories to return (default: 20)
    tags: Optional tags to filter by (case-insensitive)
    since: Optional ISO timestamp to filter memories after this date

Returns:
    Dictionary with list of memories and total count


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `limit` | integer |  |  |
| `tags` | unknown |  |  |
| `since` | unknown |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "ListMemories",
    "description": "List stored memories with optional filtering.\n\nArgs:\n    limit: Maximum number of memories to return (default: 20)\n    tags: Optional tags to filter by (case-insensitive)\n    since: Optional ISO timestamp to filter memories after this date\n\nReturns:\n    Dictionary with list of memories and total count\n",
    "parameters": {
      "type": "object",
      "properties": {
        "limit": {
          "default": 20,
          "title": "Limit",
          "type": "integer"
        },
        "tags": {
          "anyOf": [
            {
              "items": {
                "type": "string"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Tags"
        },
        "since": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Since"
        }
      },
      "required": []
    }
  }
}
```

</details>

---

## 25. DeleteMemory

**Description:** Delete a memory by ID.

Args:
    memory_id: The ID of the memory to delete

Returns:
    Dictionary with success status


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `memory_id` | string | ✓ |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "DeleteMemory",
    "description": "Delete a memory by ID.\n\nArgs:\n    memory_id: The ID of the memory to delete\n\nReturns:\n    Dictionary with success status\n",
    "parameters": {
      "type": "object",
      "properties": {
        "memory_id": {
          "title": "Memory Id",
          "type": "string"
        }
      },
      "required": [
        "memory_id"
      ]
    }
  }
}
```

</details>

---

## 26. ClearAllMemories

**Description:** Clear all memories from the database.

WARNING: This is irreversible!

Returns:
    Dictionary with count of deleted memories


**Parameters:** None

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "ClearAllMemories",
    "description": "Clear all memories from the database.\n\nWARNING: This is irreversible!\n\nReturns:\n    Dictionary with count of deleted memories\n",
    "parameters": {
      "type": "object",
      "properties": {},
      "required": []
    }
  }
}
```

</details>

---

## 27. GitStatus

**Description:** Get the git status of the workspace.

Shows modified, staged, and untracked files.

Returns:
    Dictionary with git status output


**Parameters:** None

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GitStatus",
    "description": "Get the git status of the workspace.\n\nShows modified, staged, and untracked files.\n\nReturns:\n    Dictionary with git status output\n",
    "parameters": {
      "type": "object",
      "properties": {},
      "required": []
    }
  }
}
```

</details>

---

## 28. GitDiff

**Description:** Show changes to files in the workspace.

Args:
    path: Optional path to specific file (relative to workspace)
    staged: If True, show staged changes (git diff --cached)

Returns:
    Dictionary with diff output


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | unknown |  |  |
| `staged` | boolean |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GitDiff",
    "description": "Show changes to files in the workspace.\n\nArgs:\n    path: Optional path to specific file (relative to workspace)\n    staged: If True, show staged changes (git diff --cached)\n\nReturns:\n    Dictionary with diff output\n",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Path"
        },
        "staged": {
          "default": false,
          "title": "Staged",
          "type": "boolean"
        }
      },
      "required": []
    }
  }
}
```

</details>

---

## 29. GitAdd

**Description:** Stage files for commit.

Args:
    path: Path to add (default: "." for all files)

Returns:
    Dictionary with operation result


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GitAdd",
    "description": "Stage files for commit.\n\nArgs:\n    path: Path to add (default: \".\" for all files)\n\nReturns:\n    Dictionary with operation result\n",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "default": ".",
          "title": "Path",
          "type": "string"
        }
      },
      "required": []
    }
  }
}
```

</details>

---

## 30. GitCommit

**Description:** Commit staged changes with a message.

Args:
    message: Commit message

Returns:
    Dictionary with commit result


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `message` | string | ✓ |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GitCommit",
    "description": "Commit staged changes with a message.\n\nArgs:\n    message: Commit message\n\nReturns:\n    Dictionary with commit result\n",
    "parameters": {
      "type": "object",
      "properties": {
        "message": {
          "title": "Message",
          "type": "string"
        }
      },
      "required": [
        "message"
      ]
    }
  }
}
```

</details>

---

## 31. GitLog

**Description:** Show commit history.

Args:
    limit: Number of commits to show (default: 10)

Returns:
    Dictionary with log output


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `limit` | integer |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GitLog",
    "description": "Show commit history.\n\nArgs:\n    limit: Number of commits to show (default: 10)\n\nReturns:\n    Dictionary with log output\n",
    "parameters": {
      "type": "object",
      "properties": {
        "limit": {
          "default": 10,
          "title": "Limit",
          "type": "integer"
        }
      },
      "required": []
    }
  }
}
```

</details>

---

## 32. GitReset

**Description:** Reset workspace to a specific commit.

WARNING: --hard will discard all uncommitted changes!

Args:
    commit: Commit hash or reference (default: "HEAD")
    hard: If True, perform hard reset (discard changes)

Returns:
    Dictionary with reset result


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `commit` | string |  |  |
| `hard` | boolean |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GitReset",
    "description": "Reset workspace to a specific commit.\n\nWARNING: --hard will discard all uncommitted changes!\n\nArgs:\n    commit: Commit hash or reference (default: \"HEAD\")\n    hard: If True, perform hard reset (discard changes)\n\nReturns:\n    Dictionary with reset result\n",
    "parameters": {
      "type": "object",
      "properties": {
        "commit": {
          "default": "HEAD",
          "title": "Commit",
          "type": "string"
        },
        "hard": {
          "default": false,
          "title": "Hard",
          "type": "boolean"
        }
      },
      "required": []
    }
  }
}
```

</details>

---

## 33. GitRestore

**Description:** Restore a file to its committed state.

Discards uncommitted changes to the specified file.

Args:
    path: Path to file to restore

Returns:
    Dictionary with restore result


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | ✓ |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GitRestore",
    "description": "Restore a file to its committed state.\n\nDiscards uncommitted changes to the specified file.\n\nArgs:\n    path: Path to file to restore\n\nReturns:\n    Dictionary with restore result\n",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "title": "Path",
          "type": "string"
        }
      },
      "required": [
        "path"
      ]
    }
  }
}
```

</details>

---

## 34. GitBranch

**Description:** List git branches.

Args:
    list_all: If True, list all branches including remote

Returns:
    Dictionary with branch list


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `list_all` | boolean |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GitBranch",
    "description": "List git branches.\n\nArgs:\n    list_all: If True, list all branches including remote\n\nReturns:\n    Dictionary with branch list\n",
    "parameters": {
      "type": "object",
      "properties": {
        "list_all": {
          "default": true,
          "title": "List All",
          "type": "boolean"
        }
      },
      "required": []
    }
  }
}
```

</details>

---

## 35. GitCheckout

**Description:** Switch to a different branch or commit.

Args:
    branch_or_commit: Branch name or commit hash
    create_new: If True, create a new branch

Returns:
    Dictionary with checkout result


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `branch_or_commit` | string | ✓ |  |
| `create_new` | boolean |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GitCheckout",
    "description": "Switch to a different branch or commit.\n\nArgs:\n    branch_or_commit: Branch name or commit hash\n    create_new: If True, create a new branch\n\nReturns:\n    Dictionary with checkout result\n",
    "parameters": {
      "type": "object",
      "properties": {
        "branch_or_commit": {
          "title": "Branch Or Commit",
          "type": "string"
        },
        "create_new": {
          "default": false,
          "title": "Create New",
          "type": "boolean"
        }
      },
      "required": [
        "branch_or_commit"
      ]
    }
  }
}
```

</details>

---

## 36. GitBlame

**Description:** Show git blame for a file (who changed each line).

Args:
    path: File path relative to workspace

Returns:
    Dictionary with blame output


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | ✓ |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GitBlame",
    "description": "Show git blame for a file (who changed each line).\n\nArgs:\n    path: File path relative to workspace\n\nReturns:\n    Dictionary with blame output\n",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "title": "Path",
          "type": "string"
        }
      },
      "required": [
        "path"
      ]
    }
  }
}
```

</details>

---

## 37. GitBranchCreate

**Description:** Create new branch.

Args:
    name: Branch name
    from_branch: Create from this branch (default: current)

Returns:
    Dictionary with result


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | ✓ |  |
| `from_branch` | unknown |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GitBranchCreate",
    "description": "Create new branch.\n\nArgs:\n    name: Branch name\n    from_branch: Create from this branch (default: current)\n\nReturns:\n    Dictionary with result\n",
    "parameters": {
      "type": "object",
      "properties": {
        "name": {
          "title": "Name",
          "type": "string"
        },
        "from_branch": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "From Branch"
        }
      },
      "required": [
        "name"
      ]
    }
  }
}
```

</details>

---

## 38. GitListBranches

**Description:** List branches.

Args:
    all_branches: Include remote branches (default: False)

Returns:
    Dictionary with branches list


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `all_branches` | boolean |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GitListBranches",
    "description": "List branches.\n\nArgs:\n    all_branches: Include remote branches (default: False)\n\nReturns:\n    Dictionary with branches list\n",
    "parameters": {
      "type": "object",
      "properties": {
        "all_branches": {
          "default": false,
          "title": "All Branches",
          "type": "boolean"
        }
      },
      "required": []
    }
  }
}
```

</details>

---

## 39. GitPush

**Description:** Push to remote safely.

Args:
    remote: Remote name (default: origin)
    branch: Branch to push (default: current)
    force_with_lease: Safe force push (default: False)

Returns:
    Dictionary with push result


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `remote` | string |  |  |
| `branch` | unknown |  |  |
| `force_with_lease` | boolean |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GitPush",
    "description": "Push to remote safely.\n\nArgs:\n    remote: Remote name (default: origin)\n    branch: Branch to push (default: current)\n    force_with_lease: Safe force push (default: False)\n\nReturns:\n    Dictionary with push result\n",
    "parameters": {
      "type": "object",
      "properties": {
        "remote": {
          "default": "origin",
          "title": "Remote",
          "type": "string"
        },
        "branch": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Branch"
        },
        "force_with_lease": {
          "default": false,
          "title": "Force With Lease",
          "type": "boolean"
        }
      },
      "required": []
    }
  }
}
```

</details>

---

## 40. GitPull

**Description:** Pull from remote with rebase (no merge).

Args:
    remote: Remote name (default: origin)
    branch: Branch to pull (default: main)

Returns:
    Dictionary with pull result


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `remote` | string |  |  |
| `branch` | string |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GitPull",
    "description": "Pull from remote with rebase (no merge).\n\nArgs:\n    remote: Remote name (default: origin)\n    branch: Branch to pull (default: main)\n\nReturns:\n    Dictionary with pull result\n",
    "parameters": {
      "type": "object",
      "properties": {
        "remote": {
          "default": "origin",
          "title": "Remote",
          "type": "string"
        },
        "branch": {
          "default": "main",
          "title": "Branch",
          "type": "string"
        }
      },
      "required": []
    }
  }
}
```

</details>

---

## 41. GitShow

**Description:** Show commit details.

Args:
    commit: Commit hash or ref (default: HEAD)
    summarize: Show summary only (no full diff)

Returns:
    Dictionary with commit info


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `commit` | string |  |  |
| `summarize` | boolean |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GitShow",
    "description": "Show commit details.\n\nArgs:\n    commit: Commit hash or ref (default: HEAD)\n    summarize: Show summary only (no full diff)\n\nReturns:\n    Dictionary with commit info\n",
    "parameters": {
      "type": "object",
      "properties": {
        "commit": {
          "default": "HEAD",
          "title": "Commit",
          "type": "string"
        },
        "summarize": {
          "default": false,
          "title": "Summarize",
          "type": "boolean"
        }
      },
      "required": []
    }
  }
}
```

</details>

---

## 42. GitStash

**Description:** Stash operations.

Args:
    subaction: Action (push, pop, list, apply, drop)
    name: Stash name for push (optional)
    message: Stash message (optional)

Returns:
    Dictionary with stash result


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `subaction` | string | ✓ |  |
| `name` | unknown |  |  |
| `message` | unknown |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GitStash",
    "description": "Stash operations.\n\nArgs:\n    subaction: Action (push, pop, list, apply, drop)\n    name: Stash name for push (optional)\n    message: Stash message (optional)\n\nReturns:\n    Dictionary with stash result\n",
    "parameters": {
      "type": "object",
      "properties": {
        "subaction": {
          "title": "Subaction",
          "type": "string"
        },
        "name": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Name"
        },
        "message": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Message"
        }
      },
      "required": [
        "subaction"
      ]
    }
  }
}
```

</details>

---

## 43. GetTeamMembers

**Description:** Get all members of a specific team.

Args:
    team_name: Name of the team (e.g., 'datahub', 'platform', 'frontend', 'backend')

Returns:
    JSON string with team members


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `team_name` | string | ✓ |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GetTeamMembers",
    "description": "Get all members of a specific team.\n\nArgs:\n    team_name: Name of the team (e.g., 'datahub', 'platform', 'frontend', 'backend')\n\nReturns:\n    JSON string with team members\n",
    "parameters": {
      "type": "object",
      "properties": {
        "team_name": {
          "title": "Team Name",
          "type": "string"
        }
      },
      "required": [
        "team_name"
      ]
    }
  }
}
```

</details>

---

## 44. ListAllTeams

**Description:** List all available teams.

Returns:
    JSON string with all teams and their members


**Parameters:** None

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "ListAllTeams",
    "description": "List all available teams.\n\nReturns:\n    JSON string with all teams and their members\n",
    "parameters": {
      "type": "object",
      "properties": {},
      "required": []
    }
  }
}
```

</details>

---

## 45. GetCardDetails

**Description:** Get detailed information about a specific card from mock data.

Args:
    card_id: The ID of the card to retrieve

Returns:
    JSON string with card details


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `card_id` | string | ✓ |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GetCardDetails",
    "description": "Get detailed information about a specific card from mock data.\n\nArgs:\n    card_id: The ID of the card to retrieve\n\nReturns:\n    JSON string with card details\n",
    "parameters": {
      "type": "object",
      "properties": {
        "card_id": {
          "title": "Card Id",
          "type": "string"
        }
      },
      "required": [
        "card_id"
      ]
    }
  }
}
```

</details>

---

## 46. GetBusinessmapCard

**Description:** Fetch a single card from Businessmap/Kanbanize by ID.

Args:
    card_id: The Businessmap card ID

Returns:
    JSON string with card details or error message


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `card_id` | integer | ✓ |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GetBusinessmapCard",
    "description": "Fetch a single card from Businessmap/Kanbanize by ID.\n\nArgs:\n    card_id: The Businessmap card ID\n\nReturns:\n    JSON string with card details or error message\n",
    "parameters": {
      "type": "object",
      "properties": {
        "card_id": {
          "title": "Card Id",
          "type": "integer"
        }
      },
      "required": [
        "card_id"
      ]
    }
  }
}
```

</details>

---

## 47. GetBusinessmapCardWithChildren

**Description:** Fetch a card and all its child cards recursively.

Args:
    card_id: The Businessmap card ID

Returns:
    JSON string with card hierarchy including all children


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `card_id` | integer | ✓ |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GetBusinessmapCardWithChildren",
    "description": "Fetch a card and all its child cards recursively.\n\nArgs:\n    card_id: The Businessmap card ID\n\nReturns:\n    JSON string with card hierarchy including all children\n",
    "parameters": {
      "type": "object",
      "properties": {
        "card_id": {
          "title": "Card Id",
          "type": "integer"
        }
      },
      "required": [
        "card_id"
      ]
    }
  }
}
```

</details>

---

## 48. GetBusinessmapCardsByBoard

**Description:** Get all cards for a specific board.

Args:
    board_id: Board ID (optional, uses configured default if not provided)

Returns:
    JSON string with list of cards


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `board_id` | integer |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GetBusinessmapCardsByBoard",
    "description": "Get all cards for a specific board.\n\nArgs:\n    board_id: Board ID (optional, uses configured default if not provided)\n\nReturns:\n    JSON string with list of cards\n",
    "parameters": {
      "type": "object",
      "properties": {
        "board_id": {
          "default": null,
          "title": "Board Id",
          "type": "integer"
        }
      },
      "required": []
    }
  }
}
```

</details>

---

## 49. GetBusinessmapCardsByColumn

**Description:** Get all cards in a specific column.

Args:
    board_id: Board ID (optional, uses configured default)
    column_id: Column ID (optional, uses configured default)

Returns:
    JSON string with list of cards in the column


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `board_id` | integer |  |  |
| `column_id` | integer |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GetBusinessmapCardsByColumn",
    "description": "Get all cards in a specific column.\n\nArgs:\n    board_id: Board ID (optional, uses configured default)\n    column_id: Column ID (optional, uses configured default)\n\nReturns:\n    JSON string with list of cards in the column\n",
    "parameters": {
      "type": "object",
      "properties": {
        "board_id": {
          "default": null,
          "title": "Board Id",
          "type": "integer"
        },
        "column_id": {
          "default": null,
          "title": "Column Id",
          "type": "integer"
        }
      },
      "required": []
    }
  }
}
```

</details>

---

## 50. SearchBusinessmapCardsByAssignee

**Description:** Search for cards assigned to a specific user.

Args:
    assignee_id: User's display name (e.g., "Joseph Lee") - will be looked up automatically
    board_id: Board ID (optional, uses configured default)

Returns:
    JSON string with list of assigned cards


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `assignee_id` | string | ✓ |  |
| `board_id` | integer |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "SearchBusinessmapCardsByAssignee",
    "description": "Search for cards assigned to a specific user.\n\nArgs:\n    assignee_id: User's display name (e.g., \"Joseph Lee\") - will be looked up automatically\n    board_id: Board ID (optional, uses configured default)\n\nReturns:\n    JSON string with list of assigned cards\n",
    "parameters": {
      "type": "object",
      "properties": {
        "assignee_id": {
          "title": "Assignee Id",
          "type": "string"
        },
        "board_id": {
          "default": null,
          "title": "Board Id",
          "type": "integer"
        }
      },
      "required": [
        "assignee_id"
      ]
    }
  }
}
```

</details>

---

## 51. GetBusinessmapBlockedCards

**Description:** Get all blocked cards on a board.

Args:
    board_id: Board ID (optional, uses configured default)

Returns:
    JSON string with list of blocked cards


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `board_id` | integer |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GetBusinessmapBlockedCards",
    "description": "Get all blocked cards on a board.\n\nArgs:\n    board_id: Board ID (optional, uses configured default)\n\nReturns:\n    JSON string with list of blocked cards\n",
    "parameters": {
      "type": "object",
      "properties": {
        "board_id": {
          "default": null,
          "title": "Board Id",
          "type": "integer"
        }
      },
      "required": []
    }
  }
}
```

</details>

---

## 52. GetBusinessmapBoardStructure

**Description:** Get the workflow structure for a board including columns.

Args:
    board_id: Board ID (optional, uses configured default)

Returns:
    JSON string with board structure including workflows and columns


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `board_id` | integer |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GetBusinessmapBoardStructure",
    "description": "Get the workflow structure for a board including columns.\n\nArgs:\n    board_id: Board ID (optional, uses configured default)\n\nReturns:\n    JSON string with board structure including workflows and columns\n",
    "parameters": {
      "type": "object",
      "properties": {
        "board_id": {
          "default": null,
          "title": "Board Id",
          "type": "integer"
        }
      },
      "required": []
    }
  }
}
```

</details>

---

## 53. GetBusinessmapWorkflowColumns

**Description:** Get all columns for a specific workflow.

Args:
    workflow_id: Workflow ID (optional, uses configured default)

Returns:
    JSON string with list of columns


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workflow_id` | integer |  |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GetBusinessmapWorkflowColumns",
    "description": "Get all columns for a specific workflow.\n\nArgs:\n    workflow_id: Workflow ID (optional, uses configured default)\n\nReturns:\n    JSON string with list of columns\n",
    "parameters": {
      "type": "object",
      "properties": {
        "workflow_id": {
          "default": null,
          "title": "Workflow Id",
          "type": "integer"
        }
      },
      "required": []
    }
  }
}
```

</details>

---

## 54. GetBusinessmapColumnName

**Description:** Get the name of a column by its ID.

Args:
    column_id: Column ID

Returns:
    JSON string with column name or error


**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `column_id` | integer | ✓ |  |

<details>
<summary>JSON Schema</summary>

```json
{
  "type": "function",
  "function": {
    "name": "GetBusinessmapColumnName",
    "description": "Get the name of a column by its ID.\n\nArgs:\n    column_id: Column ID\n\nReturns:\n    JSON string with column name or error\n",
    "parameters": {
      "type": "object",
      "properties": {
        "column_id": {
          "title": "Column Id",
          "type": "integer"
        }
      },
      "required": [
        "column_id"
      ]
    }
  }
}
```

</details>

---

