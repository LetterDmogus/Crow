import os
import sys
import stat
from crow.manifest import Manifest

def generate_shortcut():
    """Generates OS-specific shortcut to launch crow dashboard."""
    cwd = os.getcwd()
    if sys.platform.startswith("win"):
        path = os.path.join(cwd, "Crow Dashboard.bat")
        with open(path, "w") as f:
            f.write(f"@echo off\ncrow dashboard\npause")
    else:
        path = os.path.join(cwd, "crow-dashboard.sh")
        with open(path, "w") as f:
            f.write(f"#!/bin/bash\ncrow dashboard\nread -p 'Press enter to exit...'")
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
    print(f"[crow] Shortcut generated at {path}")

def create_ghost_file(path: str):
    """Creates a 0kb file and ensures parent directories exist."""
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, 'a'):
        os.utime(path, None)

def init_workspace(remote_files, preset=None):
    """Initializes the workspace with ghost files and updates the manifest."""
    ignore_prefixes = []
    if preset == 'laravel':
        ignore_prefixes = ['vendor/', 'node_modules/', 'storage/', '.git/']
    
    manifest = Manifest()
    workspace_dir = "workspace"
    
    for path in remote_files:
        if any(path.startswith(prefix) for prefix in ignore_prefixes):
            continue
        
        local_path = os.path.join(workspace_dir, path)
        create_ghost_file(local_path)
        # Store relative path from FTP root in manifest
        manifest.set_file(path, status="skeleton")
    
    manifest.save()
    generate_shortcut()

def check_integrity():
    """Checks for critical workspace components: .crow-manifest.json, workspace/ folder, CROW.md."""
    from crow.manifest import Manifest
    manifest = Manifest()
    results = {
        "manifest": os.path.exists(manifest.path),
        "workspace": os.path.exists("workspace"),
        "crow_md": os.path.exists("CROW.md")
    }
    return results

def fix_integrity():
    """Fixes workspace integrity issues by creating missing folders and ghost files from manifest."""
    from crow.manifest import Manifest
    manifest = Manifest()
    if not os.path.exists("workspace"):
        os.makedirs("workspace")
    
    for path, info in manifest.data.get("files", {}).items():
        local_path = os.path.join("workspace", path)
        if not os.path.exists(local_path):
            create_ghost_file(local_path)
    return True
