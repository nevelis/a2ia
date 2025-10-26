import os
import pytest
from a2ia.workspace import Workspace
from a2ia.core import set_workspace

@pytest.fixture(autouse=True)
def sandbox_ws(tmp_path, monkeypatch):
    """Force all tests to run in a temporary isolated workspace and restore afterward."""
    import subprocess
    from a2ia.core import clear_workspace
    
    # Clear any cached workspace from previous tests
    clear_workspace()
    
    original_env = os.environ.get("A2IA_WORKSPACE_PATH")
    original_cwd = os.getcwd()

    ws = Workspace.attach(tmp_path)
    set_workspace(ws)

    # Initialize git repository in sandbox
    try:
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=False)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, capture_output=True, check=False)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, capture_output=True, check=False)
    except:
        pass  # Git might not be available, that's ok

    # Monkeypatch all workspace accessors to point to the sandbox
    monkeypatch.setattr("a2ia.core.get_workspace", lambda: ws)
    monkeypatch.setattr("a2ia.tools.filesystem_tools.get_workspace", lambda: ws)
    monkeypatch.setattr("a2ia.rest_server.get_workspace", lambda: ws)
    monkeypatch.setattr("a2ia.tools.git_tools.get_workspace", lambda: ws)
    monkeypatch.setattr("a2ia.tools.shell_tools.get_workspace", lambda: ws)
    monkeypatch.setattr("a2ia.tools.ci_tools.get_workspace", lambda: ws)
    monkeypatch.setattr("a2ia.tools.git_sdlc_tools.get_workspace", lambda: ws)
    monkeypatch.setattr("a2ia.tools.terraform_tools.get_workspace", lambda: ws)
    monkeypatch.setattr("a2ia.tools.workspace_tools.get_workspace", lambda: ws)

    # Update environment + working directory
    monkeypatch.setenv("A2IA_WORKSPACE_PATH", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    yield ws

    # Restore environment and working directory
    if original_env is not None:
        monkeypatch.setenv("A2IA_WORKSPACE_PATH", original_env)
    else:
        monkeypatch.delenv("A2IA_WORKSPACE_PATH", raising=False)
    os.chdir(original_cwd)