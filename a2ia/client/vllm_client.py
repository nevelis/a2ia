"""LLM client for vLLM integration via OpenAI-compatible API."""

import httpx
import json
from typing import List, Dict, Any, Optional, AsyncIterator
from .llm_base import LLMClient


class VLLMClient(LLMClient):
    """Client for interacting with vLLM via OpenAI-compatible API."""

    def __init__(
        self,
        model: str = "mistralai/Mixtral-8x7B-Instruct-v0.1",
        base_url: str = "http://localhost:8000/v1",
        api_key: str = "EMPTY"
    ):
        """Initialize vLLM client.

        Args:
            model: Model name (should match what's loaded in vLLM)
            base_url: vLLM server URL (default: http://localhost:8000/v1)
            api_key: API key (vLLM doesn't require one by default, use "EMPTY")
        """
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Send chat request to vLLM.

        Args:
            messages: List of message dicts with role and content
            tools: Optional list of tool definitions (OpenAI format)
            temperature: Sampling temperature (default: 0.7)
            max_tokens: Maximum tokens to generate

        Returns:
            Assistant message dict with role, content, and optional tool_calls
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }

        # Add tools if provided
        if tools:
            # Convert from OpenAI format to vLLM's expected format
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()

                data = response.json()
                
                # Extract the message from OpenAI format
                choice = data["choices"][0]
                message = choice["message"]
                
                return message

            except httpx.HTTPStatusError as e:
                print(f"\n❌ vLLM rejected request:")
                print(f"   Status: {e.response.status_code}")
                print(f"   Response: {e.response.text[:500]}")
                raise
            except Exception as e:
                print(f"\n⚠️  vLLM error: {e}")
                raise

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> AsyncIterator[Dict[str, Any]]:
        """Send streaming chat request to vLLM.

        Args:
            messages: List of message dicts with role and content
            tools: Optional list of tool definitions (OpenAI format)
            temperature: Sampling temperature (default: 0.7)
            max_tokens: Maximum tokens to generate

        Yields:
            Chunks of the response. Format similar to Ollama for compatibility:
            - 'message': Partial message with 'content' and/or 'tool_calls'
            - 'done': Boolean indicating if this is the final chunk
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }

        # Add tools if provided
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                ) as response:
                    response.raise_for_status()
                    
                    # Track accumulated tool calls
                    accumulated_tool_calls = []
                    
                    async for line in response.aiter_lines():
                        if not line.strip() or not line.startswith("data: "):
                            continue
                        
                        # Remove "data: " prefix
                        data_str = line[6:]
                        
                        # Check for end of stream
                        if data_str.strip() == "[DONE]":
                            # Send final done message
                            yield {
                                "message": {"content": ""},
                                "done": True
                            }
                            break
                        
                        try:
                            chunk = json.loads(data_str)
                            
                            # Extract delta from OpenAI format
                            choice = chunk.get("choices", [{}])[0]
                            delta = choice.get("delta", {})
                            finish_reason = choice.get("finish_reason")
                            
                            # Build Ollama-compatible chunk
                            ollama_chunk = {"message": {}}
                            
                            # Handle content
                            if "content" in delta and delta["content"]:
                                ollama_chunk["message"]["content"] = delta["content"]
                            
                            # Handle tool calls
                            if "tool_calls" in delta and delta["tool_calls"]:
                                # vLLM sends tool call deltas
                                for tc_delta in delta["tool_calls"]:
                                    idx = tc_delta.get("index", 0)
                                    
                                    # Ensure we have enough space in accumulated list
                                    while len(accumulated_tool_calls) <= idx:
                                        accumulated_tool_calls.append({
                                            "id": "",
                                            "type": "function",
                                            "function": {"name": "", "arguments": ""}
                                        })
                                    
                                    # Update accumulated tool call
                                    if "id" in tc_delta:
                                        accumulated_tool_calls[idx]["id"] = tc_delta["id"]
                                    if "function" in tc_delta:
                                        func = tc_delta["function"]
                                        if "name" in func:
                                            accumulated_tool_calls[idx]["function"]["name"] += func["name"]
                                        if "arguments" in func:
                                            accumulated_tool_calls[idx]["function"]["arguments"] += func["arguments"]
                                
                                # Include accumulated tool calls in message
                                ollama_chunk["message"]["tool_calls"] = accumulated_tool_calls
                            
                            # Mark done if finished
                            ollama_chunk["done"] = finish_reason is not None
                            
                            yield ollama_chunk
                            
                        except json.JSONDecodeError:
                            # Skip invalid JSON
                            continue

            except httpx.HTTPStatusError as e:
                print(f"\n❌ vLLM rejected streaming request:")
                print(f"   Status: {e.response.status_code}")
                raise
            except Exception as e:
                print(f"\n⚠️  vLLM streaming error: {e}")
                raise

