# Fix Path Logic and Auto-Binary Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve [Errno 20/17] Not a directory during `crow scan` and force FTP binary mode by default.

**Architecture:**
1.  Update `perform_scan` to correctly identify when a scanned path is a file, avoiding recursive "index.php/index.php" paths.
2.  Update `connect` in `crow/core.py` to set FTP type to Image (Binary).
3.  Update `cmd_tail` in `crow/commands.py` to use `retrbinary` instead of `retrlines` to avoid ASCII mode issues and support `REST`.

**Tech Stack:** Python 3.8+, ftplib.

---

### Task 1: Fix Path Logic in `perform_scan`

**Files:**
- Modify: `crow/commands.py:534-613`
- Test: `tests/repro_issue.py` (already exists, will be used to verify)

- [ ] **Step 1: Update `scan_recursive` to handle file paths correctly at depth 1**

```python
            def scan_recursive(current_path, current_depth):
                if current_depth > depth:
                    return
                
                # Special check for depth 1: if it's a file, handle it and return
                if current_depth == 1:
                    try:
                        size = ftp.size(current_path)
                        if size is not None:
                            handle_file(current_path)
                            return
                    except:
                        pass # Might be a directory or server doesn't support SIZE

                items = []
                try:
                    ftp.retrlines(f"LIST {current_path}", items.append)
                except Exception:
                    # Might be a file, not a directory
                    handle_file(current_path)
                    return
                
                # If LIST returns exactly one item and its name matches current_path's basename,
                # it's likely a file (some FTP servers return the file itself when LISTing it).
                if len(items) == 1:
                    item = parse_ftp_line(items[0])
                    if item and not item['is_dir'] and item['name'] == os.path.basename(current_path):
                        handle_file(current_path)
                        return

                if not items: # Empty or file
                    # Double check if it's a file by trying to get size
                    try:
                        ftp.size(current_path)
                        handle_file(current_path)
                    except: pass
                    return

                for line in items:
                    item = parse_ftp_line(line)
                    if not item: continue
                    # Use a cleaner path join to avoid double slashes or weirdness
                    name = item['name']
                    if current_path == "" or current_path == ".":
                        full_path = name
                    else:
                        full_path = f"{current_path.rstrip('/')}/{name}".lstrip("/")
                    
                    if item['is_dir']:
                        scan_recursive(full_path, current_depth + 1)
                    else:
                        handle_file(full_path)
```

- [ ] **Step 2: Run reproduction test to verify fix**

Run: `.venv/bin/pytest tests/repro_issue.py -v -s`
Expected: PASS (and it should print "Hydrated: index.php" NOT "index.php/index.php")

- [ ] **Step 3: Commit**

```bash
git add crow/commands.py
git commit -m "fix: resolve Not a directory error in scan by checking for file at depth 1"
```

---

### Task 2: Force FTP Binary Mode by Default

**Files:**
- Modify: `crow/core.py`

- [ ] **Step 1: Set Binary mode in `connect` function**

```python
def connect(cfg: dict) -> ftplib.FTP:
    ftp = ftplib.FTP()
    # ... existing connection logic ...
    ftp.connect(host, port, timeout=timeout)
    ftp.login(cfg["user"], cfg["password"])
    
    # Force Binary mode (TYPE I)
    ftp.voidcmd('TYPE I')

    passive = cfg.get("passive", True)
    ftp.set_pasv(passive)
    return ftp
```

- [ ] **Step 2: Commit**

```bash
git add crow/core.py
git commit -m "feat: force FTP binary mode by default"
```

---

### Task 3: Fix `cmd_tail` to use Binary retrieval

**Files:**
- Modify: `crow/commands.py:185-195`

- [ ] **Step 1: Update `cmd_tail` to use `retrbinary` and handle line decoding**

```python
def cmd_tail(args):
    cfg = load_config(); session_id = getattr(args, "id", "default")
    remote = resolve_remote_path(args.remote, session_id); lines_count = int(args.lines or 20)
    try:
        ftp = connect(cfg); remote = smart_resolve(ftp, remote); size = ftp.size(remote)
        offset = max(0, size - (lines_count * 200)); 
        
        # Use binary retrieval to support REST and avoid ASCII mode errors
        data = []
        ftp.voidcmd(f"REST {offset}")
        ftp.retrbinary(f"RETR {remote}", data.append)
        ftp.quit()
        
        # Decode and split into lines
        content = b"".join(data).decode("utf-8", errors="replace")
        lines = content.splitlines()
        
        output = lines[-lines_count:]
        console.print(f"[info]Last {len(output)} lines of {remote}:[/]")
        for l in output: console.print(l)
    except Exception as e: die(f"Tail failed: {e}")
```

- [ ] **Step 2: Verify `cmd_tail` manually (or via a new test if possible)**

Since I don't have a real FTP server, I'll rely on mocking or just check it with a unit test.

- [ ] **Step 3: Commit**

```bash
git add crow/commands.py
git commit -m "fix: use retrbinary in cmd_tail to avoid ASCII mode errors"
```

---

### Task 4: Cleanup

- [ ] **Step 1: Remove reproduction test file**

Run: `rm tests/repro_issue.py`

- [ ] **Step 2: Run all tests**

Run: `.venv/bin/pytest`
