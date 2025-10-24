"""Simplified MCP client using direct JSON-RPC."""

import asyncio
import json
from typing import List, Dict, Any, Optional


class SimpleMCPClient:
    """Simple MCP client using JSON-RPC over stdio."""

    def __init__(self, server_command: List[str]):
        """Initialize simple MCP client."""
        self.server_command = server_command
        self.process: Optional[asyncio.subprocess.Process] = None
        self.connected = False
        self._request_id = 0

    async def connect(self):
        """Start MCP server and connect."""
        print("  Starting MCP server subprocess...")
        self.process = await asyncio.create_subprocess_exec(
            *self.server_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        print("  Server process started (PID:", self.process.pid, ")")

        # Give it a moment to initialize
        await asyncio.sleep(0.5)

        # Check if it's still running
        if self.process.returncode is not None:
            stderr = await self.process.stderr.read()
            raise RuntimeError(f"MCP server exited immediately: {stderr.decode()}")

        self.connected = True
        print("  ✅ Connected to MCP server")

    async def disconnect(self):
        """Disconnect from MCP server."""
        if self.process:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()
            self.process = None
        self.connected = False

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool by importing and executing it directly.

        Bypasses MCP stdio protocol - just imports and calls the tool function.
        Accepts TitleCase names from LLM and maps to snake_case functions.
        """
        # Import all tool modules
        from ..tools import filesystem_tools, git_tools, git_sdlc_tools, shell_tools, memory_tools, workspace_tools, terraform_tools, ci_tools

        # Convert TitleCase to snake_case
        import re
        snake_name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

        # Map snake_case names to functions
        tool_map = {
            # Filesystem
            "read_file": filesystem_tools.read_file,
            "write_file": filesystem_tools.write_file,
            "append_file": filesystem_tools.append_file,
            "find_replace": filesystem_tools.find_replace,
            "find_replace_regex": filesystem_tools.find_replace_regex,
            "patch_file": filesystem_tools.patch_file,
            "truncate_file": filesystem_tools.truncate_file,
            "list_directory": filesystem_tools.list_directory,
            "delete_file": filesystem_tools.delete_file,
            "prune_directory": filesystem_tools.prune_directory,
            "move_file": filesystem_tools.move_file,
            "head": filesystem_tools.head,
            "tail": filesystem_tools.tail,
            "grep": filesystem_tools.grep,
            # Git
            "git_status": git_tools.git_status,
            "git_diff": git_tools.git_diff,
            "git_add": git_tools.git_add,
            "git_commit": git_tools.git_commit,
            "git_log": git_tools.git_log,
            "git_reset": git_tools.git_reset,
            "git_restore": git_tools.git_restore,
            "git_blame": git_tools.git_blame,
            "git_checkout": git_tools.git_checkout,
            # Git SDLC
            "git_create_epoch_branch": git_sdlc_tools.git_create_epoch_branch,
            "git_rebase_main": git_sdlc_tools.git_rebase_main,
            "git_push_branch": git_sdlc_tools.git_push_branch,
            "git_squash_epoch": git_sdlc_tools.git_squash_epoch,
            "git_fast_forward_merge": git_sdlc_tools.git_fast_forward_merge,
            "git_tag_epoch_final": git_sdlc_tools.git_tag_epoch_final,
            "git_cherry_pick_phase": git_sdlc_tools.git_cherry_pick_phase,
            "workspace_sync": git_sdlc_tools.workspace_sync,
            # Shell
            "execute_command": shell_tools.execute_command,
            "execute_turk": shell_tools.execute_turk,
            "turk_info": shell_tools.turk_info,
            "turk_reset": shell_tools.turk_reset,
            # CI
            "make": ci_tools.make,
            "ruff": ci_tools.ruff,
            "black": ci_tools.black,
            "pytest_run": ci_tools.pytest_run,
            # Memory
            "store_memory": memory_tools.store_memory,
            "recall_memory": memory_tools.recall_memory,
            "list_memories": memory_tools.list_memories,
            # Workspace
            "get_workspace_info": workspace_tools.get_workspace_info,
            # Terraform
            "terraform_init": terraform_tools.terraform_init,
            "terraform_plan": terraform_tools.terraform_plan,
            "terraform_apply": terraform_tools.terraform_apply,
            "terraform_destroy": terraform_tools.terraform_destroy,
            "terraform_validate": terraform_tools.terraform_validate,
            "terraform_workspace": terraform_tools.terraform_workspace,
            "terraform_import": terraform_tools.terraform_import,
            "terraform_state": terraform_tools.terraform_state,
            "terraform_taint": terraform_tools.terraform_taint,
            "terraform_untaint": terraform_tools.terraform_untaint,
            "terraform_output": terraform_tools.terraform_output,
        }

        if snake_name not in tool_map:
            raise ValueError(f"Unknown tool: {name} (normalized to {snake_name})")

        # Call the tool
        tool_func = tool_map[snake_name]
        return await tool_func(**arguments)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools."""
        # Get all tools from A2IA by importing them
        tools = []

        # Filesystem tools (TitleCase names)
        tools.extend([
            {"type": "function", "function": {"name": "ReadFile", "description": "Read file contents", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
            {"type": "function", "function": {"name": "WriteFile", "description": "Write/overwrite file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
            {"type": "function", "function": {"name": "AppendFile", "description": "Append content to end of file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
            {"type": "function", "function": {"name": "FindReplace", "description": "Find and replace text in file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "find": {"type": "string"}, "replace": {"type": "string"}, "count": {"type": "integer"}}, "required": ["path", "find", "replace"]}}},
            {"type": "function", "function": {"name": "FindReplaceRegex", "description": "Find and replace using regex patterns", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "pattern": {"type": "string"}, "replacement": {"type": "string"}, "count": {"type": "integer"}}, "required": ["path", "pattern", "replacement"]}}},
            {"type": "function", "function": {"name": "PatchFile", "description": "Apply unified diff patch to file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "diff": {"type": "string"}}, "required": ["path", "diff"]}}},
            {"type": "function", "function": {"name": "TruncateFile", "description": "Truncate file to size (0=empty)", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "size": {"type": "integer"}}}}},
            {"type": "function", "function": {"name": "ListDirectory", "description": "List directory contents", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "recursive": {"type": "boolean"}}}}},
            {"type": "function", "function": {"name": "DeleteFile", "description": "Delete file or directory", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "recursive": {"type": "boolean"}}}}},
            {"type": "function", "function": {"name": "PruneDirectory", "description": "Delete all except matching patterns", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "keep_patterns": {"type": "array"}}, "required": ["path"]}}},
            {"type": "function", "function": {"name": "MoveFile", "description": "Move/rename file", "parameters": {"type": "object", "properties": {"source": {"type": "string"}, "destination": {"type": "string"}}, "required": ["source", "destination"]}}},
            {"type": "function", "function": {"name": "Head", "description": "Read first N lines of file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "lines": {"type": "integer"}}, "required": ["path"]}}},
            {"type": "function", "function": {"name": "Tail", "description": "Read last N lines of file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "lines": {"type": "integer"}}, "required": ["path"]}}},
            {"type": "function", "function": {"name": "Grep", "description": "Search for pattern in files", "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}, "regex": {"type": "boolean"}, "recursive": {"type": "boolean"}, "ignore_case": {"type": "boolean"}}, "required": ["pattern", "path"]}}},
        ])

        # Git tools (TitleCase names)
        tools.extend([
            {"type": "function", "function": {"name": "GitStatus", "description": "Show git status", "parameters": {"type": "object"}}},
            {"type": "function", "function": {"name": "GitDiff", "description": "Show git diff", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "staged": {"type": "boolean"}}}}},
            {"type": "function", "function": {"name": "GitAdd", "description": "Stage files for commit", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
            {"type": "function", "function": {"name": "GitCommit", "description": "Commit changes", "parameters": {"type": "object", "properties": {"message": {"type": "string"}}, "required": ["message"]}}},
            {"type": "function", "function": {"name": "GitLog", "description": "View commit history", "parameters": {"type": "object", "properties": {"limit": {"type": "integer"}}}}},
            {"type": "function", "function": {"name": "GitReset", "description": "Reset to previous commit", "parameters": {"type": "object", "properties": {"commit": {"type": "string"}, "hard": {"type": "boolean"}}}}},
            {"type": "function", "function": {"name": "GitBlame", "description": "Show who changed each line", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
            {"type": "function", "function": {"name": "GitCheckout", "description": "Switch branch or commit", "parameters": {"type": "object", "properties": {"branch_or_commit": {"type": "string"}, "create_new": {"type": "boolean"}}, "required": ["branch_or_commit"]}}},
        ])

        # Git SDLC tools (TitleCase names)
        tools.extend([
            {"type": "function", "function": {"name": "GitCreateEpochBranch", "description": "Create epoch branch from main", "parameters": {"type": "object", "properties": {"number": {"type": "integer"}, "descriptor": {"type": "string"}}, "required": ["number", "descriptor"]}}},
            {"type": "function", "function": {"name": "GitRebaseMain", "description": "Rebase onto main", "parameters": {"type": "object"}}},
            {"type": "function", "function": {"name": "GitPushBranch", "description": "Push branch to remote", "parameters": {"type": "object", "properties": {"remote": {"type": "string"}, "force": {"type": "boolean"}}}}},
            {"type": "function", "function": {"name": "GitSquashEpoch", "description": "Squash epoch commits", "parameters": {"type": "object", "properties": {"message": {"type": "string"}}, "required": ["message"]}}},
            {"type": "function", "function": {"name": "GitFastForwardMerge", "description": "Fast-forward merge to main", "parameters": {"type": "object", "properties": {"branch": {"type": "string"}}}}},
            {"type": "function", "function": {"name": "GitTagEpochFinal", "description": "Tag epoch as final", "parameters": {"type": "object", "properties": {"epoch_number": {"type": "integer"}, "message": {"type": "string"}}, "required": ["epoch_number"]}}},
            {"type": "function", "function": {"name": "GitCherryPickPhase", "description": "Cherry-pick commit", "parameters": {"type": "object", "properties": {"commit_hash": {"type": "string"}}, "required": ["commit_hash"]}}},
            {"type": "function", "function": {"name": "WorkspaceSync", "description": "Sync with remote", "parameters": {"type": "object", "properties": {"remote": {"type": "string"}}}}},
        ])

        # Shell tools (TitleCase names)
        tools.extend([
            {"type": "function", "function": {"name": "ExecuteCommand", "description": "Execute shell command (non-interactive)", "parameters": {"type": "object", "properties": {"command": {"type": "string"}, "timeout": {"type": "integer"}, "cwd": {"type": "string"}}, "required": ["command"]}}},
            {"type": "function", "function": {"name": "ExecuteTurk", "description": "Execute shell command with human operator oversight for safe execution", "parameters": {"type": "object", "properties": {"command": {"type": "string"}, "timeout": {"type": "integer"}, "cwd": {"type": "string"}}, "required": ["command"]}}},
            {"type": "function", "function": {"name": "TurkInfo", "description": "Get ExecuteTurk usage statistics", "parameters": {"type": "object"}}},
            {"type": "function", "function": {"name": "TurkReset", "description": "Reset ExecuteTurk tracking", "parameters": {"type": "object"}}},
        ])

        # CI/Testing tools (TitleCase names)
        tools.extend([
            {"type": "function", "function": {"name": "Make", "description": "Run make targets", "parameters": {"type": "object", "properties": {"target": {"type": "string"}, "makefile": {"type": "string"}}}}},
            {"type": "function", "function": {"name": "Ruff", "description": "Run Ruff linter/formatter", "parameters": {"type": "object", "properties": {"action": {"type": "string"}, "path": {"type": "string"}, "fix": {"type": "boolean"}}}}},
            {"type": "function", "function": {"name": "Black", "description": "Run Black formatter", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "check": {"type": "boolean"}}}}},
            {"type": "function", "function": {"name": "PytestRun", "description": "Run pytest tests", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "markers": {"type": "string"}, "verbose": {"type": "boolean"}, "coverage": {"type": "boolean"}}}}},
        ])

        # Memory tools (TitleCase names)
        tools.extend([
            {"type": "function", "function": {"name": "StoreMemory", "description": "Store knowledge in memory", "parameters": {"type": "object", "properties": {"content": {"type": "string"}, "tags": {"type": "array"}}, "required": ["content"]}}},
            {"type": "function", "function": {"name": "RecallMemory", "description": "Search memories", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["query"]}}},
            {"type": "function", "function": {"name": "ListMemories", "description": "List all memories", "parameters": {"type": "object", "properties": {"limit": {"type": "integer"}}}}},
        ])

        # Workspace tools (TitleCase names)
        tools.append(
            {"type": "function", "function": {"name": "GetWorkspaceInfo", "description": "Get workspace information", "parameters": {"type": "object"}}}
        )

        # Terraform tools (TitleCase names)
        tools.extend([
            {"type": "function", "function": {"name": "TerraformInit", "description": "Initialize Terraform", "parameters": {"type": "object", "properties": {"upgrade": {"type": "boolean"}}}}},
            {"type": "function", "function": {"name": "TerraformPlan", "description": "Generate execution plan", "parameters": {"type": "object", "properties": {"var_file": {"type": "string"}, "out": {"type": "string"}}}}},
            {"type": "function", "function": {"name": "TerraformApply", "description": "Apply changes (auto-approved)", "parameters": {"type": "object", "properties": {"auto_approve": {"type": "boolean"}, "plan_file": {"type": "string"}}}}},
            {"type": "function", "function": {"name": "TerraformDestroy", "description": "Destroy infrastructure", "parameters": {"type": "object", "properties": {"auto_approve": {"type": "boolean"}}}}},
            {"type": "function", "function": {"name": "TerraformValidate", "description": "Validate configuration", "parameters": {"type": "object"}}},
            {"type": "function", "function": {"name": "TerraformWorkspace", "description": "Manage workspaces", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "action": {"type": "string"}}, "required": ["name"]}}},
            {"type": "function", "function": {"name": "TerraformImport", "description": "Import existing resource", "parameters": {"type": "object", "properties": {"address": {"type": "string"}, "id": {"type": "string"}}, "required": ["address", "id"]}}},
            {"type": "function", "function": {"name": "TerraformState", "description": "Manage state", "parameters": {"type": "object", "properties": {"action": {"type": "string"}, "args": {"type": "array"}}, "required": ["action"]}}},
            {"type": "function", "function": {"name": "TerraformTaint", "description": "Mark resource for recreation", "parameters": {"type": "object", "properties": {"address": {"type": "string"}}, "required": ["address"]}}},
            {"type": "function", "function": {"name": "TerraformUntaint", "description": "Remove taint mark", "parameters": {"type": "object", "properties": {"address": {"type": "string"}}, "required": ["address"]}}},
            {"type": "function", "function": {"name": "TerraformOutput", "description": "Get output values", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}}}},
        ])

        return tools

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

        # Terraform tools (TitleCase names)
        tools.extend([
            {"type": "function", "function": {"name": "TerraformInit", "description": "Initialize Terraform", "parameters": {"type": "object", "properties": {"upgrade": {"type": "boolean"}}}}},
            {"type": "function", "function": {"name": "TerraformPlan", "description": "Generate execution plan", "parameters": {"type": "object", "properties": {"var_file": {"type": "string"}, "out": {"type": "string"}}}}},
            {"type": "function", "function": {"name": "TerraformApply", "description": "Apply changes (auto-approved)", "parameters": {"type": "object", "properties": {"auto_approve": {"type": "boolean"}, "plan_file": {"type": "string"}}}}},
            {"type": "function", "function": {"name": "TerraformDestroy", "description": "Destroy infrastructure", "parameters": {"type": "object", "properties": {"auto_approve": {"type": "boolean"}}}}},
            {"type": "function", "function": {"name": "TerraformValidate", "description": "Validate configuration", "parameters": {"type": "object"}}},
            {"type": "function", "function": {"name": "TerraformWorkspace", "description": "Manage workspaces", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "action": {"type": "string"}}, "required": ["name"]}}},
            {"type": "function", "function": {"name": "TerraformImport", "description": "Import existing resource", "parameters": {"type": "object", "properties": {"address": {"type": "string"}, "id": {"type": "string"}}, "required": ["address", "id"]}}},
            {"type": "function", "function": {"name": "TerraformState", "description": "Manage state", "parameters": {"type": "object", "properties": {"action": {"type": "string"}, "args": {"type": "array"}}, "required": ["action"]}}},
            {"type": "function", "function": {"name": "TerraformTaint", "description": "Mark resource for recreation", "parameters": {"type": "object", "properties": {"address": {"type": "string"}}, "required": ["address"]}}},
            {"type": "function", "function": {"name": "TerraformUntaint", "description": "Remove taint mark", "parameters": {"type": "object", "properties": {"address": {"type": "string"}}, "required": ["address"]}}},
            {"type": "function", "function": {"name": "TerraformOutput", "description": "Get output values", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}}}},
        ])

        return tools

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
