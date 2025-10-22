"""Tests for conversation orchestrator."""

import pytest
from unittest.mock import Mock, AsyncMock, patch


@pytest.mark.unit
class TestOrchestrator:
    """Test conversation orchestrator."""

    async def test_create_orchestrator(self):
        """Create orchestrator with LLM and MCP clients."""
        from a2ia.client.orchestrator import Orchestrator
        from a2ia.client.llm import OllamaClient
        from a2ia.client.mcp import MCPClient

        llm = OllamaClient(model="a2ia-qwen")
        mcp = MCPClient(server_command=["python3", "-m", "a2ia.server", "--mode", "mcp"])

        orch = Orchestrator(llm_client=llm, mcp_client=mcp)

        assert orch.llm_client == llm
        assert orch.mcp_client == mcp
        assert orch.messages == []

    async def test_add_user_message(self):
        """Add user message to conversation."""
        from a2ia.client.orchestrator import Orchestrator
        from a2ia.client.llm import OllamaClient
        from a2ia.client.mcp import MCPClient

        llm = OllamaClient(model="test")
        mcp = MCPClient(server_command=["echo"])

        orch = Orchestrator(llm_client=llm, mcp_client=mcp)
        orch.add_message("user", "Hello!")

        assert len(orch.messages) == 1
        assert orch.messages[0]["role"] == "user"
        assert orch.messages[0]["content"] == "Hello!"

    @patch('a2ia.client.llm.OllamaClient.chat')
    async def test_process_turn_simple(self, mock_chat):
        """Process a turn without tool calls."""
        from a2ia.client.orchestrator import Orchestrator
        from a2ia.client.llm import OllamaClient
        from a2ia.client.mcp import MCPClient

        # Mock LLM response
        mock_chat.return_value = {
            "role": "assistant",
            "content": "Hello! How can I help?"
        }

        llm = OllamaClient(model="test")
        mcp = MCPClient(server_command=["echo"])

        orch = Orchestrator(llm_client=llm, mcp_client=mcp)
        orch.add_message("user", "Hello")

        response = await orch.process_turn()

        assert response["role"] == "assistant"
        assert "help" in response["content"].lower()
        assert len(orch.messages) == 2  # user + assistant

    @patch('a2ia.client.mcp.MCPClient.call_tool')
    @patch('a2ia.client.llm.OllamaClient.chat')
    async def test_process_turn_with_tool_call(self, mock_chat, mock_call_tool):
        """Process a turn with tool call."""
        from a2ia.client.orchestrator import Orchestrator
        from a2ia.client.llm import OllamaClient
        from a2ia.client.mcp import MCPClient

        # First LLM response: tool call
        # Second LLM response: final answer
        mock_chat.side_effect = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "function": {
                            "name": "read_file",
                            "arguments": '{"path": "test.txt"}'
                        }
                    }
                ]
            },
            {
                "role": "assistant",
                "content": "The file contains: Hello!"
            }
        ]

        # Mock tool result
        mock_call_tool.return_value = {"content": "Hello!", "path": "test.txt"}

        llm = OllamaClient(model="test")
        mcp = MCPClient(server_command=["echo"])
        mcp._tools = [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read file",
                    "parameters": {}
                }
            }
        ]

        orch = Orchestrator(llm_client=llm, mcp_client=mcp)
        orch.add_message("user", "Read test.txt")

        response = await orch.process_turn()

        assert response["role"] == "assistant"
        assert "file contains" in response["content"].lower()
        mock_call_tool.assert_called_once()
