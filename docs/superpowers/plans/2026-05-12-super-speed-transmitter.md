# Super Speed Transmitter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** implement a high-speed folder sync feature using ZIP compression and a temporary PHP bridge.

**Architecture:** Use a "Pack-Ship-Trigger" pattern. Local folder is zipped, a temporary PHP bridge with a one-time token is generated, both are uploaded via FTP, and then the bridge is triggered via HTTP to extract and clean up.

**Tech Stack:** Python (zipfile, requests), PHP (ZipArchive), FTP.

---

### Task 1: Create PHP Bridge Template

**Files:**
- Create: `crow/bridge_template.php`

- [ ] **Step 1: Write the PHP Bridge Template**

```php
<?php
/**
 * Crow Speed Bridge
 * One-time use script for ZIP extraction and Smart Clean.
 */

$key = "{{KEY}}";
$zipName = "{{ZIP_NAME}}";
$targetDir = __DIR__;

if (($_GET['key'] ?? '') !== $key) {
    header('HTTP/1.1 403 Forbidden');
    echo json_encode(['success' => false, 'error' => 'Invalid key']);
    exit;
}

$report = ['deleted' => [], 'extracted' => 0, 'errors' => []];

try {
    $zip = new ZipArchive;
    if ($zip->open($zipName) === TRUE) {
        // 1. Get list of files in ZIP
        $zipFiles = [];
        for ($i = 0; $i < $zip->numFiles; $i++) {
            $zipFiles[] = $zip->getNameIndex($i);
        }

        // 2. Smart Clean: Delete files in targetDir not in ZIP
        $iterator = new RecursiveIteratorIterator(
            new RecursiveDirectoryIterator($targetDir, RecursiveDirectoryIterator::SKIP_DOTS),
            RecursiveIteratorIterator::CHILD_FIRST
        );

        foreach ($iterator as $file) {
            $relativePath = str_replace($targetDir . DIRECTORY_PATH_SEPARATOR, '', $file->getRealPath());
            
            // Don't delete the bridge or the zip itself
            if ($relativePath === basename(__FILE__) || $relativePath === $zipName) continue;
            
            if (!in_array($relativePath, $zipFiles)) {
                if ($file->isDir()) {
                    @rmdir($file->getRealPath());
                } else {
                    @unlink($file->getRealPath());
                }
                $report['deleted'][] = $relativePath;
            }
        }

        // 3. Extract All
        $zip->extractTo($targetDir);
        $report['extracted'] = $zip->numFiles;
        $zip->close();
        
        $report['success'] = true;
    } else {
        throw new Exception("Failed to open ZIP file");
    }
} catch (Exception $e) {
    $report['success'] = false;
    $report['errors'][] = $e->getMessage();
}

// 4. Self Destruct
@unlink($zipName);
@unlink(__FILE__);

header('Content-Type: application/json');
echo json_encode($report);
```

- [ ] **Step 2: Commit**
```bash
git add crow/bridge_template.php
git commit -m "feat(transmitter): add PHP bridge template"
```

---

### Task 2: Implement Local Transmitter Logic

**Files:**
- Create: `crow/transmitter.py`
- Test: `tests/test_transmitter.py`

- [ ] **Step 1: Write failing test for Zipping**
```python
import os
import zipfile
from crow.transmitter import zip_folder

def test_zip_folder(tmp_path):
    d = tmp_path / "src"
    d.mkdir()
    (d / "hello.txt").write_text("world")
    
    zip_path = tmp_path / "output.zip"
    zip_folder(str(d), str(zip_path))
    
    assert zip_path.exists()
    with zipfile.ZipFile(zip_path, 'r') as z:
        assert "hello.txt" in z.namelist()
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_transmitter.py`

- [ ] **Step 3: Implement zip_folder in `crow/transmitter.py`**
```python
import zipfile
import os
from pathlib import Path

def zip_folder(folder_path, output_path):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), folder_path)
                zipf.write(os.path.join(root, file), rel_path)
```

- [ ] **Step 4: Implement bridge generation logic**
```python
import secrets
import string

def generate_bridge(zip_name):
    key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    template_path = Path(__file__).parent / "bridge_template.php"
    with open(template_path, "r") as f:
        content = f.read()
    
    content = content.replace("{{KEY}}", key)
    content = content.replace("{{ZIP_NAME}}", zip_name)
    return content, key
```

- [ ] **Step 5: Verify tests pass**
Run: `pytest tests/test_transmitter.py`

- [ ] **Step 6: Commit**
```bash
git add crow/transmitter.py tests/test_transmitter.py
git commit -m "feat(transmitter): implement zip and bridge generation"
```

---

### Task 3: Integrate into Commands and CLI

**Files:**
- Modify: `crow/commands.py`
- Modify: `crow/cli.py`

- [ ] **Step 1: Add cmd_transmit to `crow/commands.py`**
```python
from crow.transmitter import zip_folder, generate_bridge
import requests
import tempfile

def cmd_transmit(args):
    local_dir = args.local_dir
    remote_path = args.remote_path or "."
    
    # 1. Load config and connect
    cfg = load_config()
    web_url = cfg.get("web_url")
    if not web_url:
        die("Error: 'web_url' not found in config. Required for transmitter.")

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_name = "payload.zip"
        zip_path = os.path.join(tmpdir, zip_name)
        bridge_name = "crow-bridge.php"
        bridge_path = os.path.join(tmpdir, bridge_name)
        
        # 2. Pack
        ok(f"Packing [cyan]{local_dir}[/]...")
        zip_folder(local_dir, zip_path)
        
        # 3. Generate Bridge
        content, key = generate_bridge(zip_name)
        with open(bridge_path, "w") as f:
            f.write(content)
            
        # 4. Upload
        ftp = connect(cfg)
        remote_full = resolve_remote_path(remote_path)
        try:
            ftp.cwd(remote_full)
        except:
            ftp.mkd(remote_full)
            ftp.cwd(remote_full)
            
        ok(f"Uploading to [cyan]{remote_full}[/]...")
        with open(zip_path, "rb") as f:
            ftp.storbinary(f"STOR {zip_name}", f)
        with open(bridge_path, "rb") as f:
            ftp.storbinary(f"STOR {bridge_name}", f)
        ftp.quit()
        
        # 5. Trigger
        trigger_url = f"{web_url.rstrip('/')}/{remote_full.lstrip('/')}/{bridge_name}?key={key}"
        ok(f"Triggering bridge: [dim]{trigger_url}[/]")
        
        try:
            res = requests.get(trigger_url, timeout=30)
            result = res.json()
            if result.get("success"):
                ok(f"Success! Extracted {result['extracted']} files.")
                if result['deleted']:
                    info(f"Smart Clean: Deleted {len(result['deleted'])} obsolete files.")
            else:
                die(f"Remote Error: {result.get('errors')}")
        except Exception as e:
            die(f"Trigger failed: {e}")
```

- [ ] **Step 2: Register command in `crow/cli.py`**
```python
    # transmit
    p_transmit = sub.add_parser("transmit", help="Super speed upload (ZIP + PHP)")
    p_transmit.add_argument("local_dir", help="Local directory to upload")
    p_transmit.add_argument("remote_path", nargs="?", help="Remote target path")
    p_transmit.set_defaults(func=cmd_transmit)
```

- [ ] **Step 3: Commit**
```bash
git add crow/commands.py crow/cli.py
git commit -m "feat(transmitter): add transmit command to CLI"
```
