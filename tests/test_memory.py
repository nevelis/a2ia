"""Tests for memory system with ChromaDB."""

import shutil
import tempfile

import pytest


@pytest.fixture
def temp_memory_path(monkeypatch):
    """Create a temporary memory database directory."""
    from a2ia.tools import memory_tools

    temp_dir = tempfile.mkdtemp(prefix="a2ia_memory_test_")
    monkeypatch.setenv("A2IA_MEMORY_PATH", temp_dir)

    # Reset global state BEFORE test
    memory_tools._chroma_client = None
    memory_tools._memory_collection = None
    memory_tools._current_memory_path = None

    yield temp_dir

    # Cleanup AFTER test
    try:
        memory_tools._chroma_client = None
        memory_tools._memory_collection = None
        memory_tools._current_memory_path = None
    except Exception:
        pass

    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.integration
class TestMemoryStorage:
    """Test memory storage operations."""

    async def test_store_simple_memory(self, temp_memory_path):
        """Store a simple memory."""
        from a2ia.tools.memory_tools import store_memory

        result = await store_memory("Python is a programming language")
        assert "memory_id" in result
        assert result["memory_id"].startswith("mem_")
        assert "stored_at" in result

    async def test_store_memory_with_tags(self, temp_memory_path):
        """Store memory with tags."""
        from a2ia.tools.memory_tools import store_memory

        result = await store_memory(
            "React is a JavaScript library for building UIs",
            tags=["programming", "javascript", "frontend"],
        )
        assert result["tags"] == ["programming", "javascript", "frontend"]

    async def test_store_memory_with_metadata(self, temp_memory_path):
        """Store memory with custom metadata."""
        from a2ia.tools.memory_tools import store_memory

        result = await store_memory(
            "FastAPI is a modern Python web framework",
            metadata={"source": "documentation", "confidence": "high"},
        )
        assert "memory_id" in result

    async def test_store_multiple_memories(self, temp_memory_path):
        """Store multiple memories."""
        from a2ia.tools.memory_tools import store_memory

        memories = [
            "Python is dynamically typed",
            "JavaScript runs in browsers",
            "Rust is memory safe",
        ]

        results = []
        for content in memories:
            result = await store_memory(content)
            results.append(result)

        assert len(results) == 3
        assert all(r["memory_id"].startswith("mem_") for r in results)


@pytest.mark.integration
class TestMemoryRecall:
    """Test memory recall (semantic search)."""

    async def test_recall_similar_memory(self, temp_memory_path):
        """Recall memory based on semantic similarity."""
        from a2ia.tools.memory_tools import recall_memory, store_memory

        # Store some memories
        await store_memory("Python is an interpreted programming language")
        await store_memory("JavaScript is used for web development")
        await store_memory("Bananas are yellow fruits")

        # Recall memories about programming
        result = await recall_memory("programming languages", limit=2)

        assert "memories" in result
        assert len(result["memories"]) >= 1
        assert result["memories"][0]["similarity"] > 0.5
        # Should match Python or JavaScript, not Bananas
        assert (
            "Python" in result["memories"][0]["content"]
            or "JavaScript" in result["memories"][0]["content"]
        )

    async def test_recall_with_tags(self, temp_memory_path):
        """Recall memories filtered by tags."""
        from a2ia.tools.memory_tools import recall_memory, store_memory

        # Store with tags
        await store_memory("React hooks are powerful", tags=["react", "frontend"])
        await store_memory("Vue.js is lightweight", tags=["vue", "frontend"])
        await store_memory("Django is a Python framework", tags=["python", "backend"])

        # Recall only frontend memories
        result = await recall_memory("web frameworks", limit=5, tags=["frontend"])

        assert len(result["memories"]) == 2
        for mem in result["memories"]:
            assert "frontend" in mem["tags"]

    async def test_recall_empty_database(self, temp_memory_path):
        """Recall from empty database returns empty results."""
        from a2ia.tools.memory_tools import recall_memory

        result = await recall_memory("anything", limit=5)

        assert result["memories"] == []
        assert result["count"] == 0

    async def test_recall_limit(self, temp_memory_path):
        """Recall respects limit parameter."""
        from a2ia.tools.memory_tools import recall_memory, store_memory

        # Store many memories
        for i in range(10):
            await store_memory(f"Programming fact number {i}")

        # Recall with limit
        result = await recall_memory("programming", limit=3)

        assert len(result["memories"]) <= 3


@pytest.mark.integration
class TestMemoryListing:
    """Test memory listing operations."""

    async def test_list_all_memories(self, temp_memory_path):
        """List all stored memories."""
        from a2ia.tools.memory_tools import list_memories, store_memory

        # Store some memories
        await store_memory("Memory 1")
        await store_memory("Memory 2")
        await store_memory("Memory 3")

        # List all
        result = await list_memories()

        assert result["total"] >= 3
        assert len(result["memories"]) >= 3

    async def test_list_empty_database(self, temp_memory_path):
        """List from empty database."""
        from a2ia.tools.memory_tools import list_memories

        result = await list_memories()

        assert result["total"] == 0
        assert result["memories"] == []

    async def test_list_with_limit(self, temp_memory_path):
        """List memories with limit."""
        from a2ia.tools.memory_tools import list_memories, store_memory

        # Store many memories
        for i in range(10):
            await store_memory(f"Memory {i}")

        # List with limit
        result = await list_memories(limit=5)

        assert len(result["memories"]) <= 5

    async def test_list_with_tags(self, temp_memory_path):
        """List memories filtered by tags."""
        from a2ia.tools.memory_tools import list_memories, store_memory

        # Store with different tags
        await store_memory("Frontend fact", tags=["frontend"])
        await store_memory("Backend fact", tags=["backend"])
        await store_memory("Database fact", tags=["database"])

        # List only frontend
        result = await list_memories(tags=["frontend"])

        assert all("frontend" in mem["tags"] for mem in result["memories"])


@pytest.mark.integration
class TestMemoryDeletion:
    """Test memory deletion operations."""

    async def test_delete_memory(self, temp_memory_path):
        """Delete a specific memory."""
        from a2ia.tools.memory_tools import delete_memory, list_memories, store_memory

        # Store and get ID
        stored = await store_memory("Memory to delete")
        memory_id = stored["memory_id"]

        # Delete
        result = await delete_memory(memory_id)
        assert result["success"] is True

        # Verify deleted
        all_memories = await list_memories()
        assert not any(m["memory_id"] == memory_id for m in all_memories["memories"])

    async def test_delete_nonexistent_memory(self, temp_memory_path):
        """Delete nonexistent memory handles gracefully."""
        from a2ia.tools.memory_tools import delete_memory

        result = await delete_memory("mem_nonexistent")
        # Should not crash, may return success=False or success=True
        assert "success" in result

    async def test_clear_all_memories(self, temp_memory_path):
        """Clear all memories from database."""
        from a2ia.tools.memory_tools import (
            clear_all_memories,
            list_memories,
            store_memory,
        )

        # Store several memories
        await store_memory("Memory 1")
        await store_memory("Memory 2")
        await store_memory("Memory 3")

        # Clear all
        result = await clear_all_memories()
        assert result["success"] is True
        assert result["deleted_count"] >= 3

        # Verify empty
        all_memories = await list_memories()
        assert all_memories["total"] == 0


@pytest.mark.integration
class TestMemoryWorkflows:
    """Test complete memory workflows."""

    async def test_knowledge_base_workflow(self, temp_memory_path):
        """Simulate building and querying a knowledge base."""
        from a2ia.tools.memory_tools import list_memories, recall_memory, store_memory

        # Build knowledge base
        knowledge = [
            ("Python uses indentation for code blocks", ["python", "syntax"]),
            ("JavaScript uses curly braces for blocks", ["javascript", "syntax"]),
            ("Python has dynamic typing", ["python", "types"]),
            ("TypeScript adds static typing to JavaScript", ["typescript", "types"]),
        ]

        for content, tags in knowledge:
            await store_memory(content, tags=tags)

        # Query about typing
        typing_results = await recall_memory("static vs dynamic typing", limit=3)
        assert len(typing_results["memories"]) >= 2

        # Query about syntax
        syntax_results = await recall_memory("code block syntax", limit=3)
        assert len(syntax_results["memories"]) >= 1

        # List all Python facts
        python_facts = await list_memories(tags=["python"])
        assert all("python" in m["tags"] for m in python_facts["memories"])

    async def test_session_notes_workflow(self, temp_memory_path):
        """Simulate storing and retrieving session notes."""
        from a2ia.tools.memory_tools import recall_memory, store_memory

        # Store session notes
        await store_memory(
            "User prefers functional programming style",
            tags=["preferences", "coding-style"],
            metadata={"session": "2025-01-15"},
        )
        await store_memory(
            "Project uses React and TypeScript",
            tags=["project", "tech-stack"],
            metadata={"session": "2025-01-15"},
        )
        await store_memory(
            "Database schema has users and posts tables",
            tags=["database", "schema"],
            metadata={"session": "2025-01-15"},
        )

        # Recall tech stack info
        tech_results = await recall_memory("what technologies are we using", limit=2)
        assert any(
            "React" in m["content"] or "TypeScript" in m["content"]
            for m in tech_results["memories"]
        )

        # Recall user preferences
        pref_results = await recall_memory("user preferences", limit=2)
        assert any("functional" in m["content"] for m in pref_results["memories"])

    async def test_semantic_search_quality(self, temp_memory_path):
        """Test quality of semantic search."""
        from a2ia.tools.memory_tools import recall_memory, store_memory

        # Store related concepts with different phrasing
        await store_memory("Machine learning trains models on data")
        await store_memory("AI systems learn patterns from examples")
        await store_memory("Neural networks mimic brain structure")
        await store_memory("Pizza is a popular Italian food")

        # Search for AI concepts (should NOT return pizza)
        result = await recall_memory("artificial intelligence and learning", limit=5)

        assert len(result["memories"]) >= 3
        # Pizza should have low similarity
        pizza_mem = [m for m in result["memories"] if "Pizza" in m["content"]]
        if pizza_mem:
            assert pizza_mem[0]["similarity"] < 0.7
