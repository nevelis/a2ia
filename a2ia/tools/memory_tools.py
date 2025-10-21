"""Memory system tools using ChromaDB for vector storage.

Provides semantic memory storage and retrieval for AI assistants.
"""

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.client import ClientAPI
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings

from ..core import WORKSPACE_PATH, get_mcp_app

mcp = get_mcp_app()

# ChromaDB client (lazy initialization)
_chroma_client: ClientAPI | None = None
_memory_collection: Collection | None = None
_current_memory_path: str | None = None


def _get_chroma_client() -> ClientAPI:
    """Get or create ChromaDB client."""
    global _chroma_client, _current_memory_path

    # Store memory database in workspace directory
    memory_db_path = Path(os.getenv("A2IA_MEMORY_PATH", str(WORKSPACE_PATH / "memory")))
    memory_db_path.mkdir(parents=True, exist_ok=True)
    memory_path_str = str(memory_db_path)

    # Reset client if path changed (for testing)
    if _chroma_client is not None and _current_memory_path != memory_path_str:
        _chroma_client = None
        global _memory_collection
        _memory_collection = None

    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=memory_path_str, settings=Settings(anonymized_telemetry=False)
        )
        _current_memory_path = memory_path_str

    return _chroma_client


def _get_memory_collection() -> Collection:
    """Get or create memory collection."""
    global _memory_collection
    if _memory_collection is None:
        client = _get_chroma_client()
        _memory_collection = client.get_or_create_collection(
            name="a2ia_memories",
            metadata={"description": "A2IA semantic memory storage"},
        )
    return _memory_collection


@mcp.tool()
async def store_memory(
    content: str, tags: list[str] | None = None, metadata: dict[str, Any] | None = None
) -> dict:
    """Store knowledge in the semantic memory system.

    Args:
        content: The knowledge content to store
        tags: Optional categorical tags for filtering
        metadata: Optional additional metadata

    Returns:
        Dictionary with memory_id and stored_at timestamp
    """
    collection = _get_memory_collection()

    # Generate unique memory ID
    timestamp = datetime.now(UTC)
    memory_id = f"mem_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"

    # Prepare metadata
    mem_metadata = metadata or {}
    mem_metadata["stored_at"] = timestamp.isoformat()
    if tags:
        mem_metadata["tags"] = ",".join(tags)  # Store as comma-separated string

    # Store in ChromaDB (embeddings generated automatically)
    collection.add(ids=[memory_id], documents=[content], metadatas=[mem_metadata])

    return {
        "memory_id": memory_id,
        "stored_at": mem_metadata["stored_at"],
        "tags": tags or [],
    }


@mcp.tool()
async def recall_memory(
    query: str, limit: int = 5, tags: list[str] | None = None
) -> dict:
    """Recall memories using semantic search.

    Args:
        query: The semantic search query
        limit: Maximum number of results to return (default: 5)
        tags: Optional tags to filter results

    Returns:
        Dictionary with list of matching memories
    """
    collection = _get_memory_collection()

    # Build where filter for tags
    where_filter = None
    if tags:
        # ChromaDB requires exact match for metadata filters
        # We'll filter in Python after retrieval for flexibility
        pass

    # Semantic search
    results = collection.query(query_texts=[query], n_results=limit, where=where_filter)

    # Parse results
    memories = []
    if results["ids"] and results["ids"][0]:
        for i in range(len(results["ids"][0])):
            memory_id = results["ids"][0][i]
            content = results["documents"][0][i]
            metadata = results["metadatas"][0][i] or {}
            distance = results["distances"][0][i]

            # Extract tags from metadata
            mem_tags = []
            if "tags" in metadata:
                mem_tags = metadata["tags"].split(",") if metadata["tags"] else []

            # Filter by tags if specified
            if tags:
                if not any(tag in mem_tags for tag in tags):
                    continue

            # Convert distance to similarity (ChromaDB uses L2 distance)
            # Lower distance = higher similarity
            # Normalize to 0-1 range (approximate)
            similarity = max(0.0, 1.0 - (distance / 2.0))

            memory = {
                "memory_id": memory_id,
                "content": content,
                "similarity": round(similarity, 4),
                "tags": mem_tags,
                "stored_at": metadata.get("stored_at"),
                "metadata": {
                    k: v for k, v in metadata.items() if k not in ["stored_at", "tags"]
                },
            }
            memories.append(memory)

    return {"query": query, "memories": memories, "count": len(memories)}


@mcp.tool()
async def list_memories(
    limit: int = 20, tags: list[str] | None = None, since: str | None = None
) -> dict:
    """List stored memories with optional filtering.

    Args:
        limit: Maximum number of memories to return (default: 20)
        tags: Optional tags to filter by
        since: Optional ISO timestamp to filter memories after this date

    Returns:
        Dictionary with list of memories and total count
    """
    collection = _get_memory_collection()

    # Get all memories (ChromaDB doesn't have great filtering for "list all")
    # We'll use a dummy query and filter in Python
    try:
        # Get collection count
        total_count = collection.count()

        if total_count == 0:
            return {"memories": [], "total": 0, "limit": limit}

        # Get all items (up to limit)
        results = collection.get(
            limit=min(limit, total_count), include=["documents", "metadatas"]
        )

        memories = []
        for i in range(len(results["ids"])):
            memory_id = results["ids"][i]
            content = results["documents"][i]
            metadata = results["metadatas"][i] or {}

            # Extract tags
            mem_tags = []
            if "tags" in metadata:
                mem_tags = metadata["tags"].split(",") if metadata["tags"] else []

            # Filter by tags if specified
            if tags:
                if not any(tag in mem_tags for tag in tags):
                    continue

            # Filter by timestamp if specified
            if since:
                stored_at = metadata.get("stored_at")
                if not stored_at or stored_at < since:
                    continue

            memory = {
                "memory_id": memory_id,
                "content": content,
                "tags": mem_tags,
                "stored_at": metadata.get("stored_at"),
                "metadata": {
                    k: v for k, v in metadata.items() if k not in ["stored_at", "tags"]
                },
            }
            memories.append(memory)

        return {
            "memories": memories,
            "total": total_count,
            "returned": len(memories),
            "limit": limit,
        }

    except Exception as e:
        return {
            "memories": [],
            "total": 0,
            "returned": 0,
            "limit": limit,
            "error": str(e),
        }


@mcp.tool()
async def delete_memory(memory_id: str) -> dict:
    """Delete a memory by ID.

    Args:
        memory_id: The ID of the memory to delete

    Returns:
        Dictionary with success status
    """
    collection = _get_memory_collection()

    try:
        collection.delete(ids=[memory_id])
        return {"success": True, "memory_id": memory_id}
    except Exception as e:
        return {"success": False, "memory_id": memory_id, "error": str(e)}


@mcp.tool()
async def clear_all_memories() -> dict:
    """Clear all memories from the database.

    WARNING: This is irreversible!

    Returns:
        Dictionary with count of deleted memories
    """
    collection = _get_memory_collection()

    try:
        count = collection.count()
        # Delete the collection and recreate it
        client = _get_chroma_client()
        client.delete_collection("a2ia_memories")

        # Reset global collection reference
        global _memory_collection
        _memory_collection = None

        return {"success": True, "deleted_count": count}
    except Exception as e:
        return {"success": False, "error": str(e)}
