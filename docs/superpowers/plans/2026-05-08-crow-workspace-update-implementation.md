# Crow Workspace Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `crow workspace update` to refresh core files (CROW.md, shortcuts) and bump manifest version to 2.0.1.

**Architecture:**
- `crow/cli.py`: Add `workspace update` subcommand.
- `crow/commands.py`: Implement `cmd_workspace_update` and logic to backup/refresh CROW.md.
- `crow/workspace.py`: Expose `DEFAULT_CROW_MD_CONTENT` and ensure `generate_shortcut` is reusable.
- `crow/manifest.py`: Update default version to `2.0.1`.

**Tech Stack:** Python 3.8+, ftplib.

---

### Task 1: Update CLI and Manifest Version

**Files:**
- Modify: `crow/cli.py`
- Modify: `crow/manifest.py`

- [ ] **Step 1: Add `update` subcommand to `workspace` group in CLI**

```python
# In crow/cli.py, inside build_parser() under ws_sub
    # workspace update
    ws_sub.add_parser("update", help="Refresh core files and bump manifest version")
```

- [ ] **Step 2: Update default manifest version to 2.0.1**

```python
# In crow/manifest.py, inside __init__
        self.data = {"version": "2.0.1", "files": {}}
```

- [ ] **Step 3: Run existing manifest tests to verify version bump**

Run: `.venv/bin/pytest tests/test_manifest.py`
Expected: FAIL (it currently expects 2.0.0)

- [ ] **Step 4: Update manifest tests to expect 2.0.1**

```python
# In tests/test_manifest.py
def test_manifest_init():
    manifest = Manifest()
    assert manifest.data["version"] == "2.0.1"
```

- [ ] **Step 5: Run tests again**

Run: `.venv/bin/pytest tests/test_manifest.py`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add crow/cli.py crow/manifest.py tests/test_manifest.py
git commit -m "feat: add workspace update command and bump manifest version to 2.0.1"
```

---

### Task 2: Implement Workspace Update Logic

**Files:**
- Modify: `crow/workspace.py`
- Modify: `crow/commands.py`

- [ ] **Step 1: Define `DEFAULT_CROW_MD_CONTENT` in `crow/workspace.py`**

```python
DEFAULT_CROW_MD_CONTENT = """---
auto_scan: []
scan_interval: 5
auto_yes: false
---

# Crow Project Notes
Write your project-specific notes and watcher rules here.
"""
```

- [ ] **Step 2: Implement `cmd_workspace_update` in `crow/commands.py`**

```python
def cmd_workspace_update(args):
    import os
    import shutil
    from crow.manifest import Manifest
    from crow.workspace import generate_shortcut, DEFAULT_CROW_MD_CONTENT
    
    # 1. Backup and Refresh CROW.md
    if os.path.exists("CROW.md"):
        shutil.move("CROW.md", "CROW.md.bak")
        info("Backed up CROW.md to CROW.md.bak")
    
    with open("CROW.md", "w") as f:
        f.write(DEFAULT_CROW_MD_CONTENT)
    ok("Generated latest CROW.md")

    # 2. Refresh Shortcuts
    generate_shortcut()
    ok("Refreshed OS shortcuts")

    # 3. Bump Manifest Version
    manifest = Manifest()
    old_version = manifest.data.get("version", "unknown")
    manifest.data["version"] = "2.0.1"
    manifest.save()
    ok(f"Bumped manifest version from {old_version} to 2.0.1")
```

- [ ] **Step 3: Update `cmd_workspace` dispatcher in `crow/commands.py`**

```python
def cmd_workspace(args):
    if not args.subcommand:
        # ...
    
    dispatch = {
        "init": cmd_workspace_init,
        "status": cmd_workspace_status,
        "sync": cmd_workspace_sync,
        "update": cmd_workspace_update  # Add this
    }
    # ...
```

- [ ] **Step 4: Commit**

```bash
git add crow/workspace.py crow/commands.py
git commit -m "feat: implement workspace update logic"
```

---

### Task 3: Verification and Unit Testing

**Files:**
- Create: `tests/test_workspace_update.py`

- [ ] **Step 1: Write test for `crow workspace update`**

```python
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
```

- [ ] **Step 2: Run all tests**

Run: `.venv/bin/pytest`
Expected: ALL PASS (11 tests)

- [ ] **Step 3: Commit**

```bash
git add tests/test_workspace_update.py
git commit -m "test: add workspace update verification tests"
```
