# Crow Health Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rework the Crow TUI from a dual-panel FTP browser into a Workspace Health Dashboard, including a "Dashboard Doctor" and OS-specific shortcuts.

**Architecture:**
- `crow/tui/app.py`: Reworked to be the `DashboardApp` with status-based widgets.
- `crow/tui/widgets/doctor.py`: New widget for integrity checks and auto-fixes.
- `crow/workspace.py`: Enhanced to handle shortcut generation and bulk skeleton recreation.
- `crow/cli.py`: Update commands to replace `browse` with `dashboard`.

**Tech Stack:** Python 3.8+, Textual, ftplib.

---

### Task 1: Update CLI and Workspace Helpers

**Files:**
- Modify: `crow/cli.py`
- Modify: `crow/commands.py`
- Modify: `crow/workspace.py`

- [ ] **Step 1: Replace `browse` command with `dashboard` in CLI**

```python
# In crow/cli.py
# ... update help text and subparser ...
    # dashboard (replaced browse)
    sub.add_parser("dashboard", parents=[parent_parser], help="Start health dashboard")
# ... update dispatch ...
        "dashboard": commands.cmd_dashboard,
```

- [ ] **Step 2: Update `cmd_dashboard` in `crow/commands.py`**

```python
def cmd_dashboard(args):
    from crow.tui.app import DashboardApp
    app = DashboardApp()
    app.run()

def cmd_browse(args):
    die("Command 'browse' is deprecated. Use 'crow dashboard' instead.")
```

- [ ] **Step 3: Implement Shortcut Generation in `crow/workspace.py`**

```python
import sys
import os
import stat

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

# Update init_workspace to call generate_shortcut
```

- [ ] **Step 4: Commit**

```bash
git add crow/cli.py crow/commands.py crow/workspace.py
git commit -m "feat: replace browse with dashboard and add shortcut generation"
```

---

### Task 2: Implement Dashboard Doctor Logic

**Files:**
- Modify: `crow/workspace.py`

- [ ] **Step 1: Add `check_integrity` and `fix_integrity` to `crow/workspace.py`**

```python
def check_integrity():
    from crow.manifest import Manifest
    manifest = Manifest()
    results = {
        "manifest": os.path.exists(manifest.path),
        "workspace": os.path.exists("workspace"),
        "crow_md": os.path.exists("CROW.md")
    }
    return results

def fix_integrity():
    from crow.manifest import Manifest
    manifest = Manifest()
    if not os.path.exists("workspace"):
        os.makedirs("workspace")
    
    for path, info in manifest.data.get("files", {}).items():
        local_path = os.path.join("workspace", path)
        if not os.path.exists(local_path):
            create_ghost_file(local_path)
    return True
```

- [ ] **Step 2: Commit**

```bash
git add crow/workspace.py
git commit -m "feat: add integrity check and fix logic for dashboard doctor"
```

---

### Task 3: Rework TUI App into Dashboard

**Files:**
- Modify: `crow/tui/app.py`
- Create: `crow/tui/widgets/doctor.py`

- [ ] **Step 1: Create Doctor Widget**

```python
from textual.widgets import Static, Button
from textual.containers import Vertical
from crow.workspace import check_integrity, fix_integrity

class DoctorWidget(Vertical):
    def compose(self):
        yield Static("DASHBOARD DOCTOR", classes="section-title")
        yield Static("Status: Scanning...", id="doctor-status")
        yield Button("FIX WORKSPACE", id="fix-btn", variant="primary")

    def on_mount(self):
        self.update_status()

    def update_status(self):
        res = check_integrity()
        status_text = "\n".join([f"{k.upper()}: {'✅' if v else '❌'}" for k, v in res.items()])
        self.query_one("#doctor-status", Static).update(status_text)
```

- [ ] **Step 2: Rework `DashboardApp` in `crow/tui/app.py`**

```python
# Rework App to use Header, DoctorWidget, Log for Activity, and Stats
class DashboardApp(App):
    # CSS for dashboard layout
    # BINDINGS for Fix, Refresh, Quit
    def compose(self):
        yield Header()
        with Horizontal():
            yield DoctorWidget(id="doctor")
            yield Log(id="activity-log")
        yield Footer()

    def on_mount(self):
        # Initial scan and fix if needed
        from crow.workspace import check_integrity, fix_integrity
        if not check_integrity()["workspace"]:
            fix_integrity()
            self.notify("Workspace skeleton restored!")
```

- [ ] **Step 3: Commit**

```bash
git add crow/tui/app.py crow/tui/widgets/doctor.py
git commit -m "feat: implement dashboard TUI and doctor widget"
```

---

### Task 4: Final Cleanup and Verification

- [ ] **Step 1: Remove old TUI widgets if no longer used**

```bash
rm crow/tui/widgets/file_panel.py
```

- [ ] **Step 2: Run all tests**

Run: `.venv/bin/pytest`

- [ ] **Step 3: Commit**

```bash
git commit -m "chore: cleanup old TUI files"
```
