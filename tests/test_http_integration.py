"""Integration tests for the HTTP server.

Tests all HTTP endpoints with authentication, error handling, and full workflows.
"""

import shutil
import tempfile

import pytest
from httpx import ASGITransport, AsyncClient

from a2ia.http_server import app


@pytest.fixture
def auth_headers():
    """Authentication headers for HTTP requests."""
    return {"Authorization": "Bearer poop"}


@pytest.fixture
def invalid_auth_headers():
    """Invalid authentication headers."""
    return {"Authorization": "Bearer wrong"}


@pytest.fixture
async def client():
    """HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def temp_workspace_root(monkeypatch):
    """Create a temporary workspace root directory and clear workspace state."""
    from a2ia.core import clear_workspace

    # Clear any existing workspace state
    clear_workspace()

    temp_dir = tempfile.mkdtemp(prefix="a2ia_test_")
    monkeypatch.setenv("A2IA_WORKSPACE_ROOT", temp_dir)
    yield temp_dir

    # Clean up
    clear_workspace()
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.integration
class TestHealthAndOpenAPI:
    """Test system endpoints."""

    async def test_health_check_no_auth(self, client):
        """Health check should not require authentication."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    async def test_openapi_spec(self, client):
        """OpenAPI spec should be available."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        spec = response.json()
        assert spec["info"]["title"] == "A2IA - Aaron's AI Assistant"
        assert "paths" in spec


@pytest.mark.integration
class TestAuthentication:
    """Test authentication requirements."""

    async def test_workspace_requires_auth(self, client):
        """Workspace endpoints require authentication."""
        response = await client.post("/tools/create_workspace")
        assert response.status_code == 403  # No auth header

    async def test_invalid_token_rejected(self, client, invalid_auth_headers):
        """Invalid tokens should be rejected."""
        response = await client.post(
            "/tools/create_workspace", headers=invalid_auth_headers
        )
        assert response.status_code == 401
        assert "Invalid authentication token" in response.json()["detail"]

    async def test_valid_token_accepted(
        self, client, auth_headers, temp_workspace_root
    ):
        """Valid tokens should be accepted."""
        response = await client.post("/tools/create_workspace", headers=auth_headers)
        assert response.status_code == 200


@pytest.mark.integration
class TestWorkspaceEndpoints:
    """Test workspace management endpoints."""

    async def test_create_new_workspace(
        self, client, auth_headers, temp_workspace_root
    ):
        """Get info about persistent workspace (backward compat)."""
        response = await client.post("/tools/create_workspace", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None
        assert "workspace_id" in data["result"]
        assert "path" in data["result"]
        # Note: workspace_id format doesn't matter with persistent workspace

    async def test_create_workspace_with_description(
        self, client, auth_headers, temp_workspace_root
    ):
        """Create workspace with description."""
        response = await client.post(
            "/tools/create_workspace",
            params={"description": "Test workspace"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None
        assert "workspace_id" in data["result"]

    async def test_get_workspace_info(self, client, auth_headers, temp_workspace_root):
        """Get workspace info after creation."""
        # Create workspace first
        create_response = await client.post(
            "/tools/create_workspace", headers=auth_headers
        )
        assert create_response.status_code == 200

        # Get info
        info_response = await client.get(
            "/tools/get_workspace_info", headers=auth_headers
        )
        assert info_response.status_code == 200
        data = info_response.json()
        assert data["error"] is None
        assert "workspace_id" in data["result"]
        assert "path" in data["result"]
        assert "created_at" in data["result"]

    async def test_get_workspace_info_no_workspace(
        self, client, auth_headers, temp_workspace_root
    ):
        """Workspace auto-initializes, always works."""
        # With persistent workspace, it auto-initializes
        response = await client.get("/tools/get_workspace_info", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Should work since workspace auto-initializes
        assert data["error"] is None
        assert "workspace_id" in data["result"]

    async def test_close_workspace(self, client, auth_headers, temp_workspace_root):
        """Close a workspace."""
        # Create workspace
        await client.post("/tools/create_workspace", headers=auth_headers)

        # Close it
        response = await client.post("/tools/close_workspace", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None


@pytest.mark.integration
class TestFilesystemEndpoints:
    """Test filesystem operation endpoints."""

    async def test_list_empty_directory(
        self, client, auth_headers, temp_workspace_root
    ):
        """List contents of empty workspace."""
        await client.post("/tools/create_workspace", headers=auth_headers)

        response = await client.get(
            "/tools/list_directory", params={"path": ""}, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None
        assert "files" in data["result"]
        assert "directories" in data["result"]

    async def test_write_and_read_file(self, client, auth_headers, temp_workspace_root):
        """Write a file and read it back."""
        await client.post("/tools/create_workspace", headers=auth_headers)

        # Write file
        write_response = await client.post(
            "/tools/write_file",
            json={"path": "test.txt", "content": "Hello, World!", "encoding": "utf-8"},
            headers=auth_headers,
        )
        assert write_response.status_code == 200
        write_data = write_response.json()
        assert write_data["error"] is None
        assert write_data["result"]["success"] is True

        # Read file back
        read_response = await client.get(
            "/tools/read_file", params={"path": "test.txt"}, headers=auth_headers
        )
        assert read_response.status_code == 200
        read_data = read_response.json()
        assert read_data["error"] is None
        assert read_data["result"]["content"] == "Hello, World!"

    async def test_write_file_with_newlines(
        self, client, auth_headers, temp_workspace_root
    ):
        """Write file with newlines and special characters."""
        await client.post("/tools/create_workspace", headers=auth_headers)

        content = "Line 1\nLine 2\nLine 3\n"
        write_response = await client.post(
            "/tools/write_file",
            json={"path": "multiline.txt", "content": content},
            headers=auth_headers,
        )
        assert write_response.status_code == 200

        read_response = await client.get(
            "/tools/read_file", params={"path": "multiline.txt"}, headers=auth_headers
        )
        assert read_response.status_code == 200
        assert read_response.json()["result"]["content"] == content

    async def test_write_file_creates_subdirectories(
        self, client, auth_headers, temp_workspace_root
    ):
        """Writing to nested path creates parent directories."""
        await client.post("/tools/create_workspace", headers=auth_headers)

        write_response = await client.post(
            "/tools/write_file",
            json={"path": "src/utils/helper.py", "content": "# helper"},
            headers=auth_headers,
        )
        assert write_response.status_code == 200

        read_response = await client.get(
            "/tools/read_file",
            params={"path": "src/utils/helper.py"},
            headers=auth_headers,
        )
        assert read_response.status_code == 200

    async def test_edit_file(self, client, auth_headers, temp_workspace_root):
        """Edit file content."""
        await client.post("/tools/create_workspace", headers=auth_headers)

        # Write initial file
        await client.post(
            "/tools/write_file",
            json={"path": "code.py", "content": "x = 1\ny = 2\n"},
            headers=auth_headers,
        )

        # Edit file
        edit_response = await client.post(
            "/tools/edit_file",
            json={"path": "code.py", "old_text": "x = 1", "new_text": "x = 42"},
            headers=auth_headers,
        )
        assert edit_response.status_code == 200
        assert edit_response.json()["error"] is None

        # Verify edit
        read_response = await client.get(
            "/tools/read_file", params={"path": "code.py"}, headers=auth_headers
        )
        assert "x = 42" in read_response.json()["result"]["content"]

    async def test_delete_file(self, client, auth_headers, temp_workspace_root):
        """Delete a file."""
        await client.post("/tools/create_workspace", headers=auth_headers)

        # Create file
        await client.post(
            "/tools/write_file",
            json={"path": "delete_me.txt", "content": "temp"},
            headers=auth_headers,
        )

        # Delete file
        delete_response = await client.delete(
            "/tools/delete_file", params={"path": "delete_me.txt"}, headers=auth_headers
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["error"] is None

        # Verify deleted
        read_response = await client.get(
            "/tools/read_file", params={"path": "delete_me.txt"}, headers=auth_headers
        )
        assert read_response.json()["error"] is not None

    async def test_move_file(self, client, auth_headers, temp_workspace_root):
        """Move/rename a file."""
        await client.post("/tools/create_workspace", headers=auth_headers)

        # Create file
        await client.post(
            "/tools/write_file",
            json={"path": "old.txt", "content": "data"},
            headers=auth_headers,
        )

        # Move file
        move_response = await client.post(
            "/tools/move_file",
            json={"source": "old.txt", "destination": "new.txt"},
            headers=auth_headers,
        )
        assert move_response.status_code == 200
        assert move_response.json()["error"] is None

        # Verify moved
        read_response = await client.get(
            "/tools/read_file", params={"path": "new.txt"}, headers=auth_headers
        )
        assert read_response.json()["result"]["content"] == "data"

    async def test_list_directory_recursive(
        self, client, auth_headers, temp_workspace_root
    ):
        """List directory recursively."""
        await client.post("/tools/create_workspace", headers=auth_headers)

        # Create nested structure
        await client.post(
            "/tools/write_file",
            json={"path": "a/b/c/file.txt", "content": "deep"},
            headers=auth_headers,
        )

        # List recursively
        response = await client.get(
            "/tools/list_directory",
            params={"path": "", "recursive": True},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None
        # Should contain nested directories
        assert any("a" in str(d) for d in data["result"]["directories"])


@pytest.mark.integration
class TestShellEndpoints:
    """Test shell execution endpoints."""

    async def test_execute_simple_command(
        self, client, auth_headers, temp_workspace_root
    ):
        """Execute a simple shell command."""
        await client.post("/tools/create_workspace", headers=auth_headers)

        response = await client.post(
            "/tools/execute_command",
            json={"command": "echo 'Hello from shell'"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None
        assert "Hello from shell" in data["result"]["stdout"]
        assert data["result"]["returncode"] == 0

    async def test_execute_command_with_timeout(
        self, client, auth_headers, temp_workspace_root
    ):
        """Execute command with custom timeout."""
        await client.post("/tools/create_workspace", headers=auth_headers)

        response = await client.post(
            "/tools/execute_command",
            json={"command": "echo 'fast'", "timeout": 5},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["error"] is None

    async def test_execute_command_in_subdirectory(
        self, client, auth_headers, temp_workspace_root
    ):
        """Execute command in workspace subdirectory."""
        await client.post("/tools/create_workspace", headers=auth_headers)

        # Create subdirectory with file
        await client.post(
            "/tools/write_file",
            json={"path": "subdir/test.txt", "content": "content"},
            headers=auth_headers,
        )

        # Run ls in subdirectory
        response = await client.post(
            "/tools/execute_command",
            json={"command": "ls", "cwd": "subdir"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "test.txt" in response.json()["result"]["stdout"]


@pytest.mark.integration
class TestWorkflowIntegration:
    """Test complete workflows combining multiple operations."""

    async def test_python_project_workflow(
        self, client, auth_headers, temp_workspace_root
    ):
        """Simulate creating and running a Python project."""
        # Create workspace
        ws_response = await client.post("/tools/create_workspace", headers=auth_headers)
        assert ws_response.status_code == 200

        # Write main.py
        await client.post(
            "/tools/write_file",
            json={"path": "main.py", "content": "print('Hello from Python')"},
            headers=auth_headers,
        )

        # Write test.py
        await client.post(
            "/tools/write_file",
            json={"path": "test.py", "content": "assert 1 + 1 == 2"},
            headers=auth_headers,
        )

        # List files
        list_response = await client.get(
            "/tools/list_directory", params={"path": ""}, headers=auth_headers
        )
        assert "main.py" in list_response.json()["result"]["files"]
        assert "test.py" in list_response.json()["result"]["files"]

        # Run main.py
        run_response = await client.post(
            "/tools/execute_command",
            json={"command": "python3 main.py"},
            headers=auth_headers,
        )
        assert "Hello from Python" in run_response.json()["result"]["stdout"]

        # Run test.py
        test_response = await client.post(
            "/tools/execute_command",
            json={"command": "python3 test.py"},
            headers=auth_headers,
        )
        assert test_response.json()["result"]["returncode"] == 0
