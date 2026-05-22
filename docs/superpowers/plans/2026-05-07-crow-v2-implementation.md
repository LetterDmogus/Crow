# Crow v2 — Virtual Workspace & Watching Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mengimplementasikan sistem Virtual Workspace berbasis manifest dan Watching Agent interaktif untuk sinkronisasi FTP yang cerdas.

**Architecture:** Menggunakan `.crow-manifest.json` sebagai *Single Source of Truth*. Logika sinkronisasi dipisahkan antara command manual dan background watcher menggunakan sistem file lock `.crow.lock`.

**Tech Stack:** Python 3.8+, watchdog, rich, ftplib.

---

### Task 1: Manifest Management Layer

**Files:**
- Create: `crow/manifest.py`
- Test: `tests/test_manifest.py`

- [ ] **Step 1: Define Manifest Data Structure & CRUD**
Implementasi class `Manifest` untuk mengelola data JSON.

```python
import json
import os
from typing import Dict, Any

class Manifest:
    def __init__(self, path: str = ".crow-manifest.json"):
        self.path = path
        self.data = {"version": "2.0.0", "files": {}}
        if os.path.exists(path):
            self.load()

    def load(self):
        with open(self.path, 'r') as f:
            self.data = json.load(f)

    def save(self):
        with open(self.path, 'w') as f:
            json.dump(self.data, f, indent=2)

    def set_file(self, path: str, status: str, remote_mtime: float = 0, checksum: str = ""):
        self.data["files"][path] = {
            "status": status,
            "remote_mtime": remote_mtime,
            "checksum": checksum
        }
```

- [ ] **Step 2: Write tests for Manifest**
- [ ] **Step 3: Run tests and verify**
- [ ] **Step 4: Commit**

---

### Task 2: Workspace Initialization (Ghost Files)

**Files:**
- Create: `crow/workspace.py`
- Modify: `crow/cli.py`
- Test: `tests/test_workspace.py`

- [ ] **Step 1: Implement Ghost File Creation**
Logika untuk membuat file kosong 0kb berdasarkan struktur folder.

```python
def create_ghost_file(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'a'):
        os.utime(path, None)
```

- [ ] **Step 2: Implement Laravel Preset Filter**
- [ ] **Step 3: Implement `crow workspace init` command**
- [ ] **Step 4: Verify ghost files creation with dummy FTP scan**
- [ ] **Step 5: Commit**

---

### Task 3: The Watching Agent (Interactive Mode)

**Files:**
- Create: `crow/watcher.py`
- Modify: `crow/cli.py`

- [ ] **Step 1: Integrate Watchdog for File Detection**
Setup Observer untuk memantau perubahan file di root projek.

- [ ] **Step 2: Implement Loop Prevention**
Gunakan flag internal saat upload agar watcher mengabaikan event tulis miliknya sendiri.

- [ ] **Step 3: Implement Interactive Prompt (y/n)**
Gunakan `rich.prompt` atau `input()` di terminal watcher untuk konfirmasi file baru.

- [ ] **Step 4: Test manually with `crow watch start`**
- [ ] **Step 5: Commit**

---

### Task 4: Locking & Queue Management

**Files:**
- Create: `crow/lock.py`

- [ ] **Step 1: Implement `.crow.lock` mechanism**
- [ ] **Step 2: Implement Queue Logic (Wait with Alert)**
- [ ] **Step 3: Integrate Lock into all Crow operations**
- [ ] **Step 4: Commit**

---

### Task 5: Migration v1 to v2

**Files:**
- Modify: `crow/commands.py`

- [ ] **Step 1: Implement `crow migrate`**
Scan `.ftp-tool.json` dan mapping file lokal yang ada ke manifest.
- [ ] **Step 2: Verify migration results**
- [ ] **Step 3: Commit**
