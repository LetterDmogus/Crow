import time
import ftplib
import subprocess
import os
import json
from pathlib import Path
from crow.utils import die, console

from crow.core import load_versions, save_versions, load_watchout_config, get_watchout_dir

def record_version(remote: str, size: int, modified: str):
    """Record file metadata for future conflict detection."""
    if not load_watchout_config().get("conflict_detect", True):
        return

    versions = load_versions()
    versions[remote] = {
        "size": str(size),
        "modified": modified,
        "recorded_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    save_versions(versions)

def check_conflict(ftp: ftplib.FTP, remote: str):
    """Check if remote file has changed since it was last read/recorded."""
    if not load_watchout_config().get("conflict_detect", True):
        return True

    versions = load_versions()
    if remote not in versions:
        return True # No record, assume it's okay (or first time)

    try:
        # Get current remote metadata
        # We use MDTM if available, or parse from LIST if needed.
        # Most reliable: ftp.size and MDTM
        current_size = str(ftp.size(remote))
        current_modified = ftp.voidcmd(f"MDTM {remote}")[4:].strip()
    except:
        # If MDTM fails, we might need a backup way or just skip
        return True

    recorded = versions[remote]
    if current_size != recorded["size"] or current_modified != recorded["modified"]:
        console.print(f"\n[bold red]WATCH-OUT: CONFLICT DETECTED![/]")
        console.print(f"[error]File '[cyan]{remote}[/]' has been modified on the server since you last read it.[/]")
        console.print(f"[info]Recorded: Size={recorded['size']}, Mod={recorded['modified']}[/]")
        console.print(f"[info]Remote:   Size={current_size}, Mod={current_modified}[/]")
        die("Upload aborted. Please read the file again to get the latest changes before editing.")

    return True

def make_backup(ftp: ftplib.FTP, remote: str):
    """Download existing remote file to local .crow_backups/ before overwriting/deleting."""
    backup_dir = Path.cwd() / ".crow_backups"
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    safe_name = remote.replace("/", "_").strip("_")
    local_backup_path = backup_dir / f"{safe_name}.{timestamp}.bak"
    
    try:
        with open(local_backup_path, "wb") as f:
            ftp.retrbinary(f"RETR {remote}", f.write)
        console.print(f"[dim][crow] Watch-out: existing file backed up locally to {local_backup_path}[/]")
    except ftplib.error_perm:
        if local_backup_path.exists():
            local_backup_path.unlink()
    except Exception as e:
        console.print(f"[warning][crow] Warning: Could not create local backup: {e}[/]")

def backup_folder_local(local_path: str):
    """Create a zip backup of a local folder before it gets overwritten by pull."""
    import shutil
    path = Path(local_path)
    if not path.exists():
        return

    backup_dir = Path.cwd() / ".crow_backups"
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    backup_name = backup_dir / f"local_{path.name}_{timestamp}"
    
    try:
        shutil.make_archive(str(backup_name), 'zip', str(path))
        console.print(f"[success][crow] Watch-out: Local folder backed up to {backup_name}.zip[/]")
    except Exception as e:
        console.print(f"[warning][crow] Warning: Local folder backup failed: {e}[/]")

def get_quota_file() -> Path:
    return get_watchout_dir() / "quota.json"

def track_quota(bytes_count: int, direction: str = "up"):
    """Track total bandwidth usage in the current session."""
    if not load_watchout_config().get("quota_watcher", True):
        return

    quota_path = get_quota_file()
    data = {"up": 0, "down": 0, "last_reset": time.time()}
    
    if quota_path.exists():
        try:
            with open(quota_path) as f: data = json.load(f)
        except: pass

    # Reset if older than 1 hour (auto-reset window)
    if time.time() - data.get("last_reset", 0) > 3600:
        data = {"up": 0, "down": 0, "last_reset": time.time()}

    data[direction] += bytes_count
    
    with open(quota_path, "w") as f: json.dump(data, f)

    total_mb = (data["up"] + data["down"]) / (1024 * 1024)
    if total_mb > 10: # Alert if > 10MB in an hour
        console.print(f"[bold yellow]WATCH-OUT: QUOTA REACHED![/]")
        console.print(f"[warning]Current session has moved {total_mb:.1f}MB. Consider cooling down to save bandwidth/tokens.[/]")

def ghost_file_alert(remote: str):
    """Alert when a file expected via map is missing from server."""
    console.print(f"[bold yellow]WATCH-OUT: GHOST FILE DETECTED![/]")
    console.print(f"[error]File '[cyan]{remote}[/]' was expected but is missing from the server.[/]")
    console.print(f"[info]Hint: Run 'crow map --refresh' to sync your project structure.[/]")

def log_error_alert(remote: str, new_lines: list):
    """Alert AI when new errors are detected in remote logs."""
    console.print(f"\n[bold red]WATCH-OUT: NEW REMOTE ERROR DETECTED![/]")
    console.print(f"[warning]Source: [cyan]{remote}[/][/]")
    for line in new_lines:
        if "error" in line.lower() or "fatal" in line.lower() or "exception" in line.lower():
            console.print(f"[red] > {line.strip()}[/]")
        else:
            console.print(f"[dim] > {line.strip()}[/]")

def verify_upload(ftp: ftplib.FTP, remote: str, expected_size: int) -> bool:
    """Verify that the uploaded file size matches the local size."""
    try:
        remote_size = ftp.size(remote)
        if remote_size == expected_size:
            return True
        console.print(f"[bold red]WATCH-OUT: UPLOAD INTEGRITY FAILURE![/]")
        console.print(f"[error]Remote size ({remote_size}) doesn't match expected size ({expected_size}).[/]")
        return False
    except:
        return False

def is_synced(remote: str, local_path: Path) -> bool:
    """Check if local file matches the last recorded remote version."""
    versions = load_versions()
    if remote not in versions:
        return False
    
    recorded = versions[remote]
    try:
        local_size = str(local_path.stat().st_size)
        if local_size == recorded["size"]:
            return True
    except:
        pass
    return False

def suggest_dependencies(remote: str, content: str):
    """Scan content for imports/requires and suggest related files to AI."""
    if not load_watchout_config().get("smart_context", True):
        return

    import re
    ext = Path(remote).suffix.lower()
    patterns = []
    
    if ext == ".php":
        patterns = [r"(?:require|include)(?:_once)?\s*['\"]([^'\"]+)['\"]", r"use\s+([A-Z][\w\\]+)"]
    elif ext in [".js", ".ts", ".vue"]:
        patterns = [r"import\s+.*from\s+['\"]([^'\"]+)['\"]", r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"]
    elif ext == ".py":
        patterns = [r"import\s+([\w\.]+)", r"from\s+([\w\.]+)\s+import"]

    suggestions = set()
    for p in patterns:
        matches = re.findall(p, content)
        for m in matches:
            if "/" in m or "." in m or ext == ".php": # Simple heuristic to avoid generic modules
                suggestions.add(m)

    if suggestions:
        console.print(f"[bold cyan]WATCH-OUT: SMART CONTEXT SUGGESTION[/]")
        console.print(f"[info]This file may depend on:[/] [green]{', '.join(list(suggestions)[:5])}[/]")

def validate_action(remote: str, content: str = None, force: bool = False):
    """Validate if the action is safe to perform."""
    if force:
        return True

    w_cfg = load_watchout_config()

    # 1. Protected Files
    protected = [".htaccess", ".env", "wp-config.php", ".ftp-tool.json"]
    filename = Path(remote).name
    if filename in protected:
        die(f"File '{filename}' is protected. Use --force to modify/delete it.")

    if content is not None:
        # 2. Empty Content Check
        if not content.strip():
            die("Aborting: Content is empty or only whitespace. Use --force if intended.")

        # 3. Sensitive Data Scan (Watch-out: Leak Prevention)
        if w_cfg.get("sensitive_data_scan", True):
            sensitive_patterns = [
            r"API_KEY\s*=\s*['\"][^'\"]+['\"]",
            r"PASSWORD\s*=\s*['\"][^'\"]+['\"]",
            r"SECRET_KEY\s*=\s*['\"][^'\"]+['\"]",
            r"sk-ant-[\w-]{50,}", # Anthropic
            r"AIza[0-9A-Za-z-_]{35}", # Google API Key
            r"sq0csp-[0-9A-Za-z-_]{32}", # Square
            r"access_key_id\s*=\s*['\"][A-Z0-9]{20}['\"]", # AWS
        ]
        import re
        for pattern in sensitive_patterns:
            if re.search(pattern, content, re.IGNORECASE) and not force:
                console.print(f"[bold yellow]WATCH-OUT: SENSITIVE DATA DETECTED![/]")
                console.print(f"[warning]Found potential secret or API key in the content.[/]")
                die("Upload blocked for safety. Use --force if this is intentional.")

        # 4. Shell Escaping Warning
        if "$" in content and "\\" + "$" not in content and "content" not in content:
            console.print("[warning][crow] WARNING: Detected '$' symbol without escaping. If this was passed as a shell argument, it might be broken. Prefer using STDIN (piping) for safety.[/]")

        # 5. Syntax & Linting
        if w_cfg.get("syntax_guard", True):
            ext = Path(remote).suffix.lower()
        
        # PHP Linting
        if ext == ".php":
            with subprocess.Popen(['php', '-l'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
                stdout, stderr = proc.communicate(input=content.encode())
                if proc.returncode != 0:
                    die(f"PHP Syntax Error detected via 'php -l':\n{stderr.decode().strip()}\nUpload aborted to prevent server crash.")
        
        # Python syntax check
        if ext == ".py":
            import ast
            try:
                ast.parse(content)
            except SyntaxError as e:
                die(f"Python Syntax Error detected: {e}. Upload aborted.")

        # JSON syntax check (Watch-out: Config Protection)
        if ext == ".json":
            import json
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                die(f"JSON Syntax Error detected: {e}. Upload aborted to prevent config corruption.")

    # 6. Root & Systemic Protection (Watch-out: Core Safety)
    systemic_files = ["index.php", "wp-config.php", "init.php", ".htaccess", "web.config"]
    remote_path = Path(remote)
    if (remote_path.parent == Path("/") or remote_path.name in systemic_files) and not force:
        # Only warn on write/delete (content is None for delete, but validate_action is called)
        # We don't want to die here, just ask for force if it's a systemic file
        pass 

    return True
