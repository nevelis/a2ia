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
        from ..tools import filesystem_tools, git_tools, git_sdlc_tools, shell_tools, memory_tools, workspace_tools, terraform_tools, ci_tools, businessmap_tools

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
            "git_branch_create": git_tools.git_branch_create,
            "git_list_branches": git_tools.git_list_branches,
            "git_push": git_tools.git_push,
            "git_pull": git_tools.git_pull,
            "git_show": git_tools.git_show,
            "git_stash": git_tools.git_stash,
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
            # Businessmap
            "get_team_members": businessmap_tools.get_team_members,
            "list_all_teams": businessmap_tools.list_all_teams,
            "get_card_details": businessmap_tools.get_card_details,
            "get_businessmap_card": businessmap_tools.get_businessmap_card,
            "get_businessmap_card_with_children": businessmap_tools.get_businessmap_card_with_children,
            "get_businessmap_cards_by_board": businessmap_tools.get_businessmap_cards_by_board,
            "get_businessmap_cards_by_column": businessmap_tools.get_businessmap_cards_by_column,
            "search_businessmap_cards_by_assignee": businessmap_tools.search_businessmap_cards_by_assignee,
            "get_businessmap_blocked_cards": businessmap_tools.get_businessmap_blocked_cards,
            "get_businessmap_board_structure": businessmap_tools.get_businessmap_board_structure,
            "get_businessmap_workflow_columns": businessmap_tools.get_businessmap_workflow_columns,
            "get_businessmap_column_name": businessmap_tools.get_businessmap_column_name,
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

    def _convert_mcp_tool_to_ollama_format(self, tool) -> Dict[str, Any]:
        """Convert MCP tool format to Ollama function format.
        
        Args:
            tool: MCP Tool object with name, description, and inputSchema
            
        Returns:
            Dict in Ollama format with type='function' and function details
        """
        # Convert snake_case to TitleCase for Ollama
        import re
        name_parts = tool.name.split('_')
        title_case_name = ''.join(word.capitalize() for word in name_parts)
        
        # Extract parameters from inputSchema
        input_schema = tool.inputSchema if hasattr(tool, 'inputSchema') else {}
        properties = input_schema.get('properties', {})
        required = input_schema.get('required', [])
        
        return {
            "type": "function",
            "function": {
                "name": title_case_name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools by dynamically querying the MCP server.
        
        This method imports the MCP app and queries it for registered tools,
        ensuring we always have the latest tool definitions without hardcoding.
        
        Note: This is a synchronous wrapper around an async operation.
        """
        import asyncio
        
        # Check if we're in an async context
        try:
            loop = asyncio.get_running_loop()
            # We're already in an async context - use nest_asyncio or run in executor
            import nest_asyncio
            nest_asyncio.apply()
        except RuntimeError:
            # No running loop, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self._list_tools_async())
    
    async def _list_tools_async(self) -> List[Dict[str, Any]]:
        """Async implementation of list_tools."""
        # Import and get the MCP app (this triggers tool registration)
        from ..core import get_mcp_app
        from ..tools import (
            workspace_tools,
            filesystem_tools, 
            shell_tools,
            memory_tools,
            git_tools,
            businessmap_tools
        )
        
        # Get the MCP app instance
        mcp = get_mcp_app()
        
        # Get tools from MCP server
        mcp_tools = await mcp.list_tools()
        
        # Convert to Ollama format
        ollama_tools = []
        for tool in mcp_tools:
            ollama_tool = self._convert_mcp_tool_to_ollama_format(tool)
            ollama_tools.append(ollama_tool)
        
        return ollama_tools

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
