"""Base LLM client interface for A2IA."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator


class LLMClient(ABC):
    """Abstract base class for LLM clients.
    
    All LLM backends (Ollama, vLLM, OpenAI, etc.) should implement this interface
    to ensure they can be used interchangeably in A2IA's orchestrator.
    """

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Send chat request to LLM.

        Args:
            messages: List of message dicts with role and content
            tools: Optional list of tool definitions (OpenAI format)
            temperature: Sampling temperature (default: 0.7)

        Returns:
            Assistant message dict with role, content, and optional tool_calls
        """
        pass

    @abstractmethod
    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7
    ) -> AsyncIterator[Dict[str, Any]]:
        """Send streaming chat request to LLM.

        Args:
            messages: List of message dicts with role and content
            tools: Optional list of tool definitions (OpenAI format)
            temperature: Sampling temperature (default: 0.7)

        Yields:
            Chunks of the response as they arrive. Format:
            - 'message': Partial message with 'content' and/or 'tool_calls'
            - 'done': Boolean indicating if this is the final chunk
        """
        pass

