"""Tests for RESTful API."""

import shutil
import tempfile

import pytest
from httpx import ASGITransport, AsyncClient

from a2ia.rest_server import app


@pytest.fixture
def auth_headers():
    """Authentication headers."""
    return {"Authorization": "Bearer poop"}


@pytest.fixture
async def client():
    """HTTP client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def temp_workspace(monkeypatch):
    """Temporary workspace for testing."""
    from a2ia.core import clear_workspace

    clear_workspace()

    temp_dir = tempfile.mkdtemp(prefix="a2ia_rest_test_")
    monkeypatch.setenv("A2IA_WORKSPACE_PATH", temp_dir)
    yield temp_dir

    clear_workspace()
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.integration
class TestRESTWorkspace:
    """Test workspace endpoints."""

    async def test_get_workspace_info(self, client, auth_headers, temp_workspace):
        """Get workspace information."""
        response = await client.get("/workspace", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "workspace_id" in data
        assert "path" in data

    async def test_health_no_auth(self, client):
        """Health check doesn't need auth."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["api_style"] == "REST"


@pytest.mark.integration
class TestRESTFiles:
    """Test RESTful file operations."""

    async def test_put_and_get_file(self, client, auth_headers, temp_workspace):
        """PUT to create file, GET to read it."""
        # Write file (JSON format with content field)
        write_response = await client.put(
            "/workspace/files/test.txt",
            headers=auth_headers,
            json={"content": "Hello REST!"}
        )
        if write_response.status_code != 200:
            print(f"Error: {write_response.status_code}")
            print(f"Response: {write_response.text}")
        assert write_response.status_code == 200
        assert write_response.json()["success"] is True

        # Read file
        read_response = await client.get(
            "/workspace/files/test.txt", headers=auth_headers
        )
        assert read_response.status_code == 200
        assert read_response.text == "Hello REST!"

    async def test_patch_file_with_diff(self, client, auth_headers, temp_workspace):
        """PATCH to apply unified diff."""
        # Create initial file (JSON format)
        await client.put(
            "/workspace/files/code.py",
            headers=auth_headers,
            json={"content": "line 1\nline 2\nline 3\n"}
        )

        # Apply patch
        diff = """--- a/code.py
+++ b/code.py
@@ -1,3 +1,3 @@
 line 1
-line 2
+line 2 modified
 line 3
"""
        patch_response = await client.patch(
            "/workspace/files/code.py", headers=auth_headers, json={"diff": diff}
        )

        # Patch command might not be installed, skip if not available
        if patch_response.status_code == 500 and "patch" in patch_response.json().get(
            "detail", ""
        ):
            pytest.skip("'patch' command not available")

        assert patch_response.status_code == 200

        # Verify changes
        read_response = await client.get(
            "/workspace/files/code.py", headers=auth_headers
        )
        content = read_response.text
        assert "line 2 modified" in content
        assert "line 2\n" not in content

    async def test_delete_file(self, client, auth_headers, temp_workspace):
        """DELETE to remove file."""
        # Create file (JSON format)
        await client.put(
            "/workspace/files/delete_me.txt",
            headers=auth_headers,
            json={"content": "temporary"}
        )

        # Delete it
        delete_response = await client.delete(
            "/workspace/files/delete_me.txt", headers=auth_headers
        )
        assert delete_response.status_code == 200

        # Verify deleted
        read_response = await client.get(
            "/workspace/files/delete_me.txt", headers=auth_headers
        )
        assert read_response.status_code == 404

    async def test_list_directory(self, client, auth_headers, temp_workspace):
        """GET with ?list=true to list directory."""
        # Create files (JSON format)
        await client.put(
            "/workspace/files/file1.txt",
            headers=auth_headers,
            json={"content": "1"}
        )
        await client.put(
            "/workspace/files/file2.txt",
            headers=auth_headers,
            json={"content": "2"}
        )

        # List directory
        list_response = await client.get(
            "/workspace/files/?list=true", headers=auth_headers
        )
        assert list_response.status_code == 200
        data = list_response.json()
        assert "file1.txt" in data["files"]
        assert "file2.txt" in data["files"]

    async def test_move_file(self, client, auth_headers, temp_workspace):
        """POST /files/{path}/move to rename."""
        # Create file (JSON format)
        await client.put(
            "/workspace/files/old.txt",
            headers=auth_headers,
            json={"content": "data"}
        )

        # Move it
        move_response = await client.post(
            "/workspace/files/old.txt/move",
            headers=auth_headers,
            json={"destination": "new.txt"},
        )
        assert move_response.status_code == 200

        # Verify
        get_new = await client.get("/workspace/files/new.txt", headers=auth_headers)
        assert get_new.status_code == 200
        assert get_new.text == "data"

        get_old = await client.get("/workspace/files/old.txt", headers=auth_headers)
        assert get_old.status_code == 404


@pytest.mark.integration
class TestRESTShell:
    """Test shell execution."""

    async def test_execute_command(self, client, auth_headers, temp_workspace):
        """POST /workspace/exec to run command."""
        response = await client.post(
            "/workspace/exec",
            headers=auth_headers,
            json={"command": "echo 'Hello Shell'"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["returncode"] == 0
        assert "Hello Shell" in data["stdout"]


@pytest.mark.integration
class TestRESTGit:
    """Test Git operations."""

    async def test_git_status(self, client, auth_headers, temp_workspace):
        """GET /workspace/git/status."""
        response = await client.get("/workspace/git/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

    async def test_git_workflow(self, client, auth_headers, temp_workspace):
        """Test complete git workflow."""
        # Create file (JSON format)
        await client.put(
            "/workspace/files/main.py",
            headers=auth_headers,
            json={"content": "print('hello')"}
        )

        # Stage
        add_response = await client.post(
            "/workspace/git/add", headers=auth_headers, json={"path": "."}
        )
        assert add_response.status_code == 200

        # Commit
        commit_response = await client.post(
            "/workspace/git/commit",
            headers=auth_headers,
            json={"message": "Add main.py"},
        )
        assert commit_response.status_code == 200

        # View log
        log_response = await client.get(
            "/workspace/git/log?limit=5", headers=auth_headers
        )
        assert log_response.status_code == 200
        assert "Add main.py" in log_response.json()["stdout"]


@pytest.mark.integration
class TestRESTMemory:
    """Test memory operations."""

    async def test_store_and_search_memory(self, client, auth_headers, temp_workspace):
        """POST to store, GET /search to recall."""
        # Store
        store_response = await client.post(
            "/memory",
            headers=auth_headers,
            json={"content": "REST APIs are awesome", "tags": ["api", "rest"]},
        )
        assert store_response.status_code == 200
        assert "memory_id" in store_response.json()

        # Search
        search_response = await client.get(
            "/memory/search?q=REST%20API&limit=3", headers=auth_headers
        )
        assert search_response.status_code == 200
        data = search_response.json()
        assert len(data["memories"]) > 0

    async def test_list_memories(self, client, auth_headers, temp_workspace):
        """GET /memory to list."""
        response = await client.get("/memory?limit=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "memories" in data
