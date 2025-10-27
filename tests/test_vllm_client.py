"""Tests for vLLM client integration."""

import pytest
import json
from unittest.mock import AsyncMock, Mock, patch
from a2ia.client.vllm_client import VLLMClient


@pytest.fixture
def vllm_client():
    """Create a vLLM client for testing."""
    return VLLMClient(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        base_url="http://localhost:8000/v1"
    )


@pytest.mark.asyncio
async def test_vllm_client_chat_basic(vllm_client):
    """Test basic chat completion without tools."""
    messages = [
        {"role": "user", "content": "Hello, how are you?"}
    ]
    
    mock_response = {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "I'm doing well, thank you!"
            }
        }]
    }
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_http_response = Mock()
        mock_http_response.json.return_value = mock_response
        mock_http_response.raise_for_status = Mock()
        mock_client.post = AsyncMock(return_value=mock_http_response)
        
        result = await vllm_client.chat(messages)
        
        assert result["role"] == "assistant"
        assert result["content"] == "I'm doing well, thank you!"
        
        # Verify the request was made correctly
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "http://localhost:8000/v1/chat/completions"
        
        payload = call_args[1]["json"]
        assert payload["model"] == "mistralai/Mixtral-8x7B-Instruct-v0.1"
        assert payload["messages"] == messages
        assert payload["stream"] is False


@pytest.mark.asyncio
async def test_vllm_client_chat_with_tools(vllm_client):
    """Test chat completion with tool definitions."""
    messages = [
        {"role": "user", "content": "What files are in the current directory?"}
    ]
    
    tools = [{
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files in a directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path"}
                }
            }
        }
    }]
    
    mock_response = {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "list_directory",
                        "arguments": json.dumps({"path": "."})
                    }
                }]
            }
        }]
    }
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_http_response = Mock()
        mock_http_response.json.return_value = mock_response
        mock_http_response.raise_for_status = Mock()
        mock_client.post = AsyncMock(return_value=mock_http_response)
        
        result = await vllm_client.chat(messages, tools=tools)
        
        assert result["role"] == "assistant"
        assert "tool_calls" in result
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["function"]["name"] == "list_directory"
        
        # Verify tools were included in request
        payload = mock_client.post.call_args[1]["json"]
        assert "tools" in payload
        assert payload["tool_choice"] == "auto"


@pytest.mark.asyncio
async def test_vllm_client_streaming_basic(vllm_client):
    """Test streaming chat completion."""
    messages = [
        {"role": "user", "content": "Count to three"}
    ]
    
    # Simulate streaming response chunks (OpenAI SSE format)
    stream_chunks = [
        'data: {"choices":[{"delta":{"role":"assistant","content":"One"},"finish_reason":null}]}\n\n',
        'data: {"choices":[{"delta":{"content":", two"},"finish_reason":null}]}\n\n',
        'data: {"choices":[{"delta":{"content":", three"},"finish_reason":"stop"}]}\n\n',
        'data: [DONE]\n\n'
    ]
    
    async def mock_aiter_lines():
        for chunk in stream_chunks:
            yield chunk.strip()
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_stream_response = AsyncMock()
        mock_stream_response.raise_for_status = Mock()
        mock_stream_response.aiter_lines = mock_aiter_lines
        mock_stream_response.__aenter__ = AsyncMock(return_value=mock_stream_response)
        mock_stream_response.__aexit__ = AsyncMock()
        
        mock_client.stream = Mock(return_value=mock_stream_response)
        
        chunks = []
        async for chunk in vllm_client.stream_chat(messages):
            chunks.append(chunk)
        
        # Verify we got content chunks
        assert len(chunks) > 0
        
        # Verify last chunk is marked as done
        assert chunks[-1]["done"] is True
        
        # Collect all content
        content = "".join(
            chunk.get("message", {}).get("content", "")
            for chunk in chunks
            if "message" in chunk
        )
        assert "One" in content
        assert "two" in content
        assert "three" in content


@pytest.mark.asyncio
async def test_vllm_client_streaming_with_tool_calls(vllm_client):
    """Test streaming with tool call deltas."""
    messages = [
        {"role": "user", "content": "List files"}
    ]
    
    # Simulate tool call streaming (accumulated deltas)
    stream_chunks = [
        'data: {"choices":[{"delta":{"role":"assistant","tool_calls":[{"index":0,"id":"call_123","type":"function","function":{"name":"list_directory","arguments":""}}]},"finish_reason":null}]}\n\n',
        'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":"{\\"path"}}]},"finish_reason":null}]}\n\n',
        'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":"\\": \\".\\"}"}}]},"finish_reason":"tool_calls"}]}\n\n',
        'data: [DONE]\n\n'
    ]
    
    async def mock_aiter_lines():
        for chunk in stream_chunks:
            yield chunk.strip()
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_stream_response = AsyncMock()
        mock_stream_response.raise_for_status = Mock()
        mock_stream_response.aiter_lines = mock_aiter_lines
        mock_stream_response.__aenter__ = AsyncMock(return_value=mock_stream_response)
        mock_stream_response.__aexit__ = AsyncMock()
        
        mock_client.stream = Mock(return_value=mock_stream_response)
        
        chunks = []
        async for chunk in vllm_client.stream_chat(messages):
            chunks.append(chunk)
        
        # Find chunk with tool calls
        tool_call_chunks = [
            c for c in chunks 
            if "message" in c and "tool_calls" in c["message"]
        ]
        
        assert len(tool_call_chunks) > 0
        
        # Verify tool call was accumulated correctly
        final_chunk = tool_call_chunks[-1]
        tool_calls = final_chunk["message"]["tool_calls"]
        assert len(tool_calls) == 1
        assert tool_calls[0]["function"]["name"] == "list_directory"
        # Arguments should be accumulated
        assert "path" in tool_calls[0]["function"]["arguments"]


@pytest.mark.asyncio
async def test_vllm_client_inherits_llm_client():
    """Test that VLLMClient properly implements LLMClient interface."""
    from a2ia.client.llm_base import LLMClient
    
    client = VLLMClient()
    
    # Should be an instance of the base class
    assert isinstance(client, LLMClient)
    
    # Should have required methods
    assert hasattr(client, 'chat')
    assert hasattr(client, 'stream_chat')
    assert callable(client.chat)
    assert callable(client.stream_chat)


@pytest.mark.asyncio
async def test_ollama_client_inherits_llm_client():
    """Test that OllamaClient also properly implements LLMClient interface."""
    from a2ia.client.llm_base import LLMClient
    from a2ia.client.llm import OllamaClient
    
    client = OllamaClient()
    
    # Should be an instance of the base class
    assert isinstance(client, LLMClient)
    
    # Should have required methods
    assert hasattr(client, 'chat')
    assert hasattr(client, 'stream_chat')
    assert callable(client.chat)
    assert callable(client.stream_chat)


def test_vllm_client_initialization():
    """Test VLLMClient can be initialized with correct defaults."""
    client = VLLMClient()
    
    assert client.model == "mistralai/Mixtral-8x7B-Instruct-v0.1"
    assert client.base_url == "http://localhost:8000/v1"
    assert client.api_key == "EMPTY"
    
    # Test custom initialization
    client = VLLMClient(
        model="custom/model",
        base_url="http://example.com:9000/v1",
        api_key="test-key"
    )
    
    assert client.model == "custom/model"
    assert client.base_url == "http://example.com:9000/v1"
    assert client.api_key == "test-key"

