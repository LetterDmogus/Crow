import time
import ftplib
import subprocess
import os
from pathlib import Path
from crow.utils import die, console

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
        console.print(f"[dim][crow] Safeguard: existing file backed up locally to {local_backup_path}[/]")
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
        console.print(f"[success][crow] Safeguard: Local folder backed up to {backup_name}.zip[/]")
    except Exception as e:
        console.print(f"[warning][crow] Warning: Local folder backup failed: {e}[/]")

def validate_action(remote: str, content: str = None, force: bool = False):
    """Validate if the action is safe to perform."""
    if force:
        return True

    # 1. Protected Files
    protected = [".htaccess", ".env", "wp-config.php", ".ftp-tool.json"]
    filename = Path(remote).name
    if filename in protected:
        die(f"File '{filename}' is protected. Use --force to modify/delete it.")

    if content is not None:
        # 2. Empty Content Check
        if not content.strip():
            die("Aborting: Content is empty or only whitespace. Use --force if intended.")

        # 3. Shell Escaping Warning (if content passed as arg, not via STDIN)
        # Detecting unescaped $ or ` in a suspicious way
        if "$" in content and "\\" + "$" not in content and "content" not in content:
            console.print("[warning][crow] WARNING: Detected '$' symbol without escaping. If this was passed as a shell argument, it might be broken. Prefer using STDIN (piping) for safety.[/]")

        # 4. Syntax & Linting
        ext = Path(remote).suffix.lower()
        
        # PHP Linting (if php is installed)
        if ext == ".php":
            # Temporary file for linting
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

    return True
