import os
import pytest
from crow.commands import cmd_workspace_update
from crow.manifest import Manifest
from types import SimpleNamespace

def test_workspace_update(tmp_path):
    os.chdir(tmp_path)
    # Setup initial state (v2.0.0)
    with open(".crow-manifest.json", "w") as f:
        f.write('{"version": "2.0.0", "files": {}}')
    with open("CROW.md", "w") as f:
        f.write("Old content")
    
    # Run update
    cmd_workspace_update(SimpleNamespace())
    
    # Verify backup
    assert os.path.exists("CROW.md.bak")
    with open("CROW.md.bak") as f:
        assert f.read() == "Old content"
    
    # Verify new content
    with open("CROW.md") as f:
        assert "# Crow Project Notes" in f.read()
    
    # Verify shortcuts (mocked or just check existence)
    if os.name == 'nt':
        assert os.path.exists("Crow Dashboard.bat")
    else:
        assert os.path.exists("crow-dashboard.sh")
        
    # Verify version bump
    manifest = Manifest()
    assert manifest.data["version"] == "2.0.1"
