import os
import pytest
from a2ia.workspace import Workspace
from a2ia.core import set_workspace

@pytest.fixture(autouse=True)
def sandbox_ws(tmp_path, monkeypatch):
    """Force all tests to run in a temporary isolated workspace and restore afterward."""
    original_env = os.environ.get("A2IA_WORKSPACE_PATH")
    original_cwd = os.getcwd()

    ws = Workspace.attach(tmp_path)
    set_workspace(ws)

    # Monkeypatch all workspace accessors to point to the sandbox
    monkeypatch.setattr("a2ia.core.get_workspace", lambda: ws)
    monkeypatch.setattr("a2ia.tools.filesystem_tools.get_workspace", lambda: ws)

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