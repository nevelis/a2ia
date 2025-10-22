"""LLM client for Ollama integration."""

import httpx
from typing import List, Dict, Any, Optional


class OllamaClient:
    """Client for interacting with Ollama LLM."""

    def __init__(
        self,
        model: str = "qwen2.5:latest",
        base_url: str = "http://localhost:11434"
    ):
        """Initialize Ollama client.

        Args:
            model: Ollama model name (default: qwen2.5:latest)
            base_url: Ollama server URL (default: http://localhost:11434)
        """
        self.model = model
        self.base_url = base_url.rstrip('/')

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Send chat request to Ollama.

        Args:
            messages: List of message dicts with role and content
            tools: Optional list of tool definitions (OpenAI format)
            temperature: Sampling temperature (default: 0.7)

        Returns:
            Assistant message dict with role, content, and optional tool_calls
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }

        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()

                data = response.json()
                return data["message"]

            except httpx.HTTPStatusError as e:
                # Show what was rejected
                print(f"\n❌ Ollama rejected request:")
                print(f"   Status: {e.response.status_code}")
                print(f"   Response: {e.response.text[:500]}")
                print(f"   Last message role: {messages[-1]['role']}")
                print(f"   Message count: {len(messages)}")
                raise
            except Exception as e:
                # Debug: show full response
                print(f"\n⚠️  Response debug:")
                print(f"   Data: {data}")
                print(f"   Message: {data.get('message')}")
                raise

    async def list_models(self) -> List[str]:
        """List available Ollama models.

        Returns:
            List of model names
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()

            data = response.json()
            return [model["name"] for model in data.get("models", [])]

    async def pull_model(self, model: str) -> bool:
        """Pull a model from Ollama registry.

        Args:
            model: Model name to pull

        Returns:
            True if successful
        """
        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await client.post(
                f"{self.base_url}/api/pull",
                json={"name": model, "stream": False}
            )
            response.raise_for_status()
            return True
