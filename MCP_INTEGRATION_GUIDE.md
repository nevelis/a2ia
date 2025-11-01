# A2IA MCP Integration Guide

This guide explains how to integrate A2IA as an MCP server with Claude Code or Claude Desktop.

## Current Status

✅ **77 tools registered** across 9 tool modules:
- Workspace tools (3)
- Filesystem tools (13)
- Git tools (17)
- Git SDLC tools (8)
- Memory tools (5)
- Shell tools (4)
- CI/CD tools (4)
- Terraform tools (11)
- Businessmap tools (12)

✅ **1 resource**: `businessmap://config`
✅ **1 prompt**: `summarize_team_work`

## Configuration for Claude Code

### Option 1: Add to your Claude Code settings

Add this to your MCP server configuration:

```json
{
  "mcpServers": {
    "a2ia": {
      "command": "/home/aaron/dev/nevelis/a2ia/.venv/bin/python",
      "args": ["-m", "a2ia.server", "--mode", "mcp"],
      "env": {
        "A2IA_WORKSPACE_PATH": "/home/aaron/dev/nevelis/a2ia/workspace"
      }
    }
  }
}
```

### Option 2: Use the example config

Copy `mcp_config_example.json` and customize the paths for your setup.

## Environment Variables

- `A2IA_WORKSPACE_PATH`: Working directory for file operations (default: `.`)
- `A2IA_MEMORY_PATH`: Directory for ChromaDB memory storage (default: `$A2IA_WORKSPACE_PATH/memory`)
- `A2IA_PASSWORD`: API password for HTTP mode (not used in MCP mode)
- `BUSINESSMAP_API_KEY`: Businessmap/Kanbanize API key (optional)
- `BUSINESSMAP_SUBDOMAIN`: Businessmap subdomain (optional)

## Testing the Server

### 1. Test tool registration

```bash
python -c "from a2ia.mcp_server import *; from a2ia.core import get_mcp_app; mcp = get_mcp_app(); print(f'Tools: {len(mcp._tool_manager._tools)}')"
```

Expected output: `Tools: 77`

### 2. Test server startup

```bash
python -m a2ia.server --mode mcp
```

The server will wait for stdio input (MCP protocol). Press Ctrl+C to exit.

### 3. Test with MCP Inspector (if available)

```bash
npx @modelcontextprotocol/inspector python -m a2ia.server --mode mcp
```

## Available Tool Categories

### Workspace Management
- `create_workspace()` - Get workspace info (backward compatibility)
- `get_workspace_info()` - Get current workspace details
- `close_workspace()` - No-op (workspace is persistent)

### File Operations
- `read_file(path)` - Read file content
- `write_file(path, content)` - Write content to file
- `delete_file(path, recursive)` - Delete file or directory
- `move_file(source, destination)` - Move/rename file
- `list_directory(path, recursive)` - List files
- `append_file(path, content)` - Append to file
- `truncate_file(path, length)` - Truncate file
- `patch_file(path, diff)` - Apply unified diff patch
- `find_replace(path, find_text, replace_text)` - Find/replace text
- `find_replace_regex(path, pattern, replace_text)` - Regex find/replace
- `head(path, lines)` - Get first N lines
- `tail(path, lines)` - Get last N lines
- `grep(pattern, path, regex, recursive, ignore_case)` - Search files
- `prune_directory(path, keep_patterns, dry_run)` - Clean directory

### Git Operations
- `git_status()` - Show git status
- `git_diff(path, staged)` - Show changes
- `git_add(paths)` - Stage files
- `git_commit(message, files)` - Create commit
- `git_log(max_count, path)` - View history
- `git_branch()` - List/create branches
- `git_checkout(branch, create)` - Switch branches
- `git_push(remote, branch, force)` - Push changes
- `git_pull(remote, branch)` - Pull changes
- `git_reset(mode, commit)` - Reset changes
- `git_restore(paths, staged)` - Restore files
- `git_stash(action, message)` - Stash changes
- `git_show(commit, path)` - Show commit/file
- `git_blame(path, start_line, end_line)` - Show blame

### Git SDLC Workflow
- `git_create_epoch_branch(epoch, phase)` - Create epoch branch
- `git_squash_epoch(epoch, phase, message)` - Squash commits
- `git_tag_epoch_final(epoch, message)` - Tag epoch completion
- `git_cherry_pick_phase(source_phase, commits)` - Cherry-pick commits
- `git_rebase_main(epoch, phase)` - Rebase onto main
- `git_fast_forward_merge(epoch, phase)` - Fast-forward merge
- `git_push_branch(epoch, phase)` - Push epoch branch
- `git_branch_create(name, start_point)` - Create branch

### Memory System
- `store_memory(content, tags, metadata)` - Store knowledge
- `recall_memory(query, limit, tags)` - Semantic search
- `list_memories(tag, limit)` - List memories
- `delete_memory(memory_id)` - Delete memory
- `clear_all_memories()` - Clear all memories

### Shell Execution
- `execute_command(command, timeout, cwd, env)` - Run shell command
- `execute_turk(command, timeout, cwd, env)` - Run with human oversight
- `turk_info()` - Get ExecuteTurk stats
- `turk_reset()` - Reset ExecuteTurk tracking

### CI/CD Tools
- `pytest_run(args, capture_output)` - Run pytest
- `ruff(command, paths, fix)` - Run ruff linter
- `black(paths, check)` - Run black formatter
- `make(target, args)` - Run make
- `workspace_sync(direction, dry_run)` - Sync workspace

### Terraform Tools
- `terraform_init(path, upgrade)` - Initialize Terraform
- `terraform_plan(path, var_file, out)` - Plan infrastructure
- `terraform_apply(path, var_file, auto_approve)` - Apply changes
- `terraform_destroy(path, var_file, auto_approve)` - Destroy infrastructure
- `terraform_validate(path)` - Validate configuration
- `terraform_workspace(action, name)` - Manage workspaces
- `terraform_state(action, args)` - Manage state
- `terraform_import(path, address, id)` - Import resources
- `terraform_taint(path, address)` - Taint resource
- `terraform_untaint(path, address)` - Untaint resource
- `terraform_output(path, name, json)` - Get outputs

### Businessmap Integration
- `get_businessmap_card(card_id)` - Get card details
- `get_businessmap_card_with_children(card_id)` - Get card with children
- `get_businessmap_cards_by_board(board_id, workflow_id)` - Get board cards
- `get_businessmap_cards_by_column(board_id, column_id)` - Get column cards
- `search_businessmap_cards_by_assignee(board_id, assignee)` - Search by assignee
- `get_businessmap_blocked_cards(board_id)` - Get blocked cards
- `get_businessmap_board_structure(board_id)` - Get board structure
- `get_businessmap_workflow_columns(workflow_id)` - Get workflow columns
- `get_businessmap_column_name(column_id)` - Get column name
- `get_team_members(team_name)` - Get team roster
- `list_all_teams()` - List all teams
- `get_card_details(card_id)` - Get mock card details

## Resources

### businessmap://config
Configuration and team roster data for Businessmap integration.

## Prompts

### summarize_team_work
Generate a summary of team work based on Businessmap cards.

## Troubleshooting

### "Command not found" error
Make sure the virtual environment is activated and the path in the config is absolute.

### "Module not found" error
Install A2IA in development mode: `pip install -e .`

### Tools not appearing
Restart Claude Code/Desktop after updating the configuration.

### Memory system not working
Check that ChromaDB is installed: `pip install chromadb sentence-transformers`

### Businessmap tools failing
Set `BUSINESSMAP_API_KEY` and `BUSINESSMAP_SUBDOMAIN` environment variables.

## Development

To add new tools:

1. Create/update tool module in `a2ia/tools/`
2. Add `@mcp.tool()` decorator to functions
3. Import the module in `a2ia/mcp_server.py`
4. Test with: `python -c "from a2ia.mcp_server import *; ..."`

See `CLAUDE.md` for detailed development patterns.
