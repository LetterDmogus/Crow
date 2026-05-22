# Workspace Initialization (Ghost Files) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the logic to initialize a virtual workspace by creating ghost files based on remote file structure.

**Architecture:** Create `crow/workspace.py` for core logic and update `crow/cli.py` and `crow/commands.py` for the user interface.

**Tech Stack:** Python, argparse, ftplib (simulated for now).

---

### Task 1: Create `crow/workspace.py` and implement `create_ghost_file`

**Files:**
- Create: `crow/workspace.py`
- Test: `tests/test_workspace.py`

- [ ] **Step 1: Write failing test for `create_ghost_file`**

```python
import os
import pytest
from crow.workspace import create_ghost_file

def test_create_ghost_file(tmp_path):
    # Change to tmp_path to avoid creating files in the project root
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        file_path = "subdir/test.txt"
        create_ghost_file(file_path)
        
        full_path = tmp_path / file_path
        assert full_path.exists()
        assert full_path.is_file()
        assert full_path.stat().st_size == 0
    finally:
        os.chdir(original_cwd)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_workspace.py::test_create_ghost_file -v`
Expected: FAIL (ModuleNotFoundError or AttributeError)

- [ ] **Step 3: Implement `create_ghost_file`**

```python
import os

def create_ghost_file(path: str):
    """Creates a 0kb file and ensures parent directories exist."""
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, 'a'):
        os.utime(path, None)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_workspace.py::test_create_ghost_file -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add crow/workspace.py tests/test_workspace.py
git commit -m "feat: add create_ghost_file to workspace"
```

### Task 2: Implement `init_workspace` in `crow/workspace.py`

**Files:**
- Modify: `crow/workspace.py`
- Test: `tests/test_workspace.py`

- [ ] **Step 1: Write failing test for `init_workspace`**

```python
import os
from crow.workspace import init_workspace
from crow.manifest import Manifest

def test_init_workspace_laravel(tmp_path):
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        remote_files = [
            "app/Models/User.php",
            "vendor/autoload.php",
            "node_modules/vue/package.json",
            "storage/logs/laravel.log",
            ".git/config",
            "public/index.php"
        ]
        
        init_workspace(remote_files, preset='laravel')
        
        assert os.path.exists("app/Models/User.php")
        assert os.path.exists("public/index.php")
        assert not os.path.exists("vendor/autoload.php")
        assert not os.path.exists("node_modules/vue/package.json")
        assert not os.path.exists("storage/logs/laravel.log")
        assert not os.path.exists(".git/config")
        
        manifest = Manifest()
        assert "app/Models/User.php" in manifest.data["files"]
        assert manifest.data["files"]["app/Models/User.php"]["status"] == "skeleton"
    finally:
        os.chdir(original_cwd)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_workspace.py::test_init_workspace_laravel -v`
Expected: FAIL (AttributeError)

- [ ] **Step 3: Implement `init_workspace`**

```python
from crow.manifest import Manifest
# Add create_ghost_file to imports if needed, but it's in the same file

def init_workspace(remote_files, preset=None):
    """Initializes the workspace with ghost files and updates the manifest."""
    ignore_prefixes = []
    if preset == 'laravel':
        ignore_prefixes = ['vendor/', 'node_modules/', 'storage/', '.git/']
    
    manifest = Manifest()
    
    for path in remote_files:
        if any(path.startswith(prefix) for prefix in ignore_prefixes):
            continue
        
        create_ghost_file(path)
        manifest.set_file(path, status="skeleton")
    
    manifest.save()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_workspace.py::test_init_workspace_laravel -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add crow/workspace.py tests/test_workspace.py
git commit -m "feat: add init_workspace to workspace"
```

### Task 3: Update `crow/cli.py` and `crow/commands.py`

**Files:**
- Modify: `crow/cli.py`
- Modify: `crow/commands.py`

- [ ] **Step 1: Add `workspace` command group to `crow/cli.py`**

In `build_parser()`:
```python
    # workspace
    p_workspace = sub.add_parser("workspace", parents=[parent_parser], help="Virtual workspace management")
    w_sub = p_workspace.add_subparsers(dest="workspace_command")
    
    w_init = w_sub.add_parser("init", parents=[parent_parser], help="Initialize workspace")
    w_init.add_argument("--preset", choices=["laravel"], help="Apply preset filters")
```

- [ ] **Step 2: Update `main` in `crow/cli.py` to handle `workspace`**

In `main()`:
```python
    dispatch = {
        # ... existing ...
        "workspace": commands.cmd_workspace,
    }
```

- [ ] **Step 3: Implement `cmd_workspace` and `cmd_workspace_init` in `crow/commands.py`**

```python
from crow.workspace import init_workspace

def cmd_workspace(args):
    if args.workspace_command == "init":
        cmd_workspace_init(args)
    else:
        # If no subcommand, print help for workspace
        # Note: argparse might already handle this if required=True, but let's be safe
        console.print("[crow] ERROR: Unknown or missing workspace command. Use 'crow workspace init'.")

def cmd_workspace_init(args):
    console.print(f"[bold magenta]=== Workspace Init ({args.preset or 'default'}) ===[/]")
    # For now, simulate remote scan as requested
    # In the future, this will come from a real FTP scan
    remote_files = [
        "app/Http/Controllers/Controller.php",
        "vendor/composer/autoload.php",
        ".env.example",
        "public/index.php"
    ]
    init_workspace(remote_files, preset=args.preset)
    ok("Workspace initialized with ghost files.")
```

- [ ] **Step 4: Verify CLI integration**

Run: `python3 -m crow.cli workspace init --preset laravel`
Expected: Successful output, `.crow-manifest.json` created, and ghost files created (excluding vendor).

- [ ] **Step 5: Commit**

```bash
git add crow/cli.py crow/commands.py
git commit -m "feat: add workspace init command"
```
