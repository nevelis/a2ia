"""Tests for LLM client (Ollama)."""

import pytest
from unittest.mock import Mock, AsyncMock, patch


@pytest.mark.unit
class TestOllamaClient:
    """Test Ollama LLM client."""

    async def test_create_client(self):
        """Create Ollama client with default settings."""
        from a2ia.client.llm import OllamaClient

        client = OllamaClient(model="qwen2.5:latest")
        assert client.model == "qwen2.5:latest"
        assert client.base_url == "http://localhost:11434"

    async def test_create_client_custom_url(self):
        """Create client with custom base URL."""
        from a2ia.client.llm import OllamaClient

        client = OllamaClient(model="llama3.1", base_url="http://192.168.1.100:11434")
        assert client.base_url == "http://192.168.1.100:11434"

    @patch('httpx.AsyncClient.post')
    async def test_chat_simple_message(self, mock_post):
        """Send simple chat message without tools."""
        from a2ia.client.llm import OllamaClient

        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you?"
            },
            "done": True
        }
        mock_post.return_value = mock_response

        client = OllamaClient(model="qwen2.5:latest")
        messages = [{"role": "user", "content": "Hello"}]

        response = await client.chat(messages)

        assert response["role"] == "assistant"
        assert "help" in response["content"].lower()
        mock_post.assert_called_once()

    @patch('httpx.AsyncClient.post')
    async def test_chat_with_tools(self, mock_post):
        """Chat with tool definitions."""
        from a2ia.client.llm import OllamaClient

        # Mock response with tool call
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "read_file",
                            "arguments": '{"path": "test.txt"}'
                        }
                    }
                ]
            },
            "done": True
        }
        mock_post.return_value = mock_response

        client = OllamaClient(model="qwen2.5:latest")
        messages = [{"role": "user", "content": "Read test.txt"}]
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"}
                        },
                        "required": ["path"]
                    }
                }
            }
        ]

        response = await client.chat(messages, tools=tools)

        assert response["role"] == "assistant"
        assert "tool_calls" in response
        assert response["tool_calls"][0]["function"]["name"] == "read_file"

    async def test_list_models(self):
        """List available Ollama models."""
        from a2ia.client.llm import OllamaClient

        client = OllamaClient()

        # This will actually call Ollama if it's running
        # For now, just test that the method exists
        assert hasattr(client, 'list_models')


@pytest.mark.integration
class TestOllamaIntegration:
    """Integration tests with real Ollama instance."""

    async def test_ollama_available(self):
        """Check if Ollama is running."""
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:11434/api/tags")
                assert response.status_code == 200
        except Exception:
            pytest.skip("Ollama not running on localhost:11434")

    async def test_simple_chat_real(self):
        """Send real chat message to Ollama."""
        from a2ia.client.llm import OllamaClient
        import httpx

        # Skip if Ollama not available
        try:
            async with httpx.AsyncClient() as http_client:
                await http_client.get("http://localhost:11434/api/tags")
        except:
            pytest.skip("Ollama not running")

        # Use a2ia-gemma or any available model
        client = OllamaClient(model="a2ia-gemma")
        messages = [{"role": "user", "content": "Say hello in 5 words or less"}]

        response = await client.chat(messages)

        assert response["role"] == "assistant"
        assert len(response["content"]) > 0
