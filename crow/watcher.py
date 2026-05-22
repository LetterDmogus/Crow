import os
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rich.prompt import Confirm
from crow.manifest import Manifest
from crow.core import connect, load_config
from crow.utils import console, ok, info
from crow.lock import CrowLock
from crow.config import load_crow_md

def run_auto_scan(interval_mins, paths):
    if not paths: return
    
    from crow.commands import perform_scan
    while True:
        time.sleep(interval_mins * 60)
        console.print(f"\n[info]Periodic Auto-Scan starting (Interval: {interval_mins}m)...[/]")
        try:
            perform_scan(paths, depth=1, do_get=False)
            console.print("[success]Periodic Auto-Scan complete.[/]")
        except Exception as e:
            console.print(f"[error]Auto-Scan failed: {e}[/]")

class CrowWatcherHandler(FileSystemEventHandler):
    def __init__(self, manifest: Manifest):
        self.manifest = manifest
        self.ignoring_files = set()
        self.cfg = load_config()
        self.lock = CrowLock()
        self.workspace_dir = "workspace"
        
        # Always Yes states
        self.always_yes_all = False
        self.always_no_all = False
        self.always_yes_dirs = set()

    def get_rel_path(self, abs_path):
        # Get path relative to current dir
        rel = os.path.relpath(abs_path, os.getcwd())
        # Strip 'workspace/' prefix to get FTP path
        if rel.startswith(self.workspace_dir + os.sep):
            return rel[len(self.workspace_dir) + 1:]
        elif rel == self.workspace_dir:
            return ""
        return None

    def is_ignored(self, ftp_path):
        if not ftp_path: return True
        # Explicitly ignore lock file and manifest
        if ".crow.lock" in ftp_path or ".crow-manifest.json" in ftp_path:
            return True
        # Ignore hidden files
        if any(part.startswith(".") for part in ftp_path.split("/")):
            return True
        return False

    def ask_decision(self, ftp_path, action="push"):
        if self.always_yes_all: return True
        if self.always_no_all: return False
        
        parent_dir = os.path.dirname(ftp_path)
        if parent_dir in self.always_yes_dirs: return True

        from rich.panel import Panel
        console.print(Panel(f"[bold]Action Required:[/] {action} [cyan]{ftp_path}[/]?"))
        choices = {
            "1": "Yes (this file only)",
            "2": f"Yes to all in '{parent_dir or 'root'}'",
            "3": "Yes to everything",
            "4": "No (skip this)",
            "5": "No to everything (quiet mode)"
        }
        for k, v in choices.items():
            console.print(f" [bold cyan]{k}[/]) {v}")
        
        try:
            ans = input("Select option [1]: ").strip() or "1"
            if ans == "1": return True
            if ans == "2":
                self.always_yes_dirs.add(parent_dir)
                return True
            if ans == "3":
                self.always_yes_all = True
                return True
            if ans == "5":
                self.always_no_all = True
                return False
            return False
        except EOFError:
            return False

    def on_modified(self, event):
        if event.is_directory:
            return
        
        ftp_path = self.get_rel_path(event.src_path)
        if self.is_ignored(ftp_path) or ftp_path in self.ignoring_files:
            if ftp_path in self.ignoring_files:
                self.ignoring_files.remove(ftp_path)
            return

        files = self.manifest.data.get("files", {})
        if ftp_path in files:
            info(f"File modified: [cyan]{ftp_path}[/]. Auto-syncing...")
            self.sync_file(ftp_path)

    def on_created(self, event):
        if event.is_directory:
            return
        
        ftp_path = self.get_rel_path(event.src_path)
        if self.is_ignored(ftp_path):
            return

        files = self.manifest.data.get("files", {})
        if ftp_path not in files:
            if self.ask_decision(ftp_path, "push"):
                self.sync_file(ftp_path)
                self.manifest.set_file(ftp_path, status="synced")
                self.manifest.save()

    def on_deleted(self, event):
        if event.is_directory:
            return
        
        ftp_path = self.get_rel_path(event.src_path)
        if self.is_ignored(ftp_path):
            return

        files = self.manifest.data.get("files", {})
        if ftp_path in files:
            if self.ask_decision(ftp_path, "delete"):
                self.delete_remote(ftp_path)
                del self.manifest.data["files"][ftp_path]
                self.manifest.save()

    def sync_file(self, ftp_path):
        local_path = os.path.join(self.workspace_dir, ftp_path)
        with self.lock:
            try:
                ftp = connect(self.cfg)
                # Ensure remote directory exists
                remote_dir = os.path.dirname(ftp_path)
                if remote_dir:
                    self.ftp_mkdirs(ftp, remote_dir)

                with open(local_path, "rb") as f:
                    ftp.storbinary(f"STOR {ftp_path}", f)

                ftp.quit()
                ok(f"Synced [green]{ftp_path}[/] to server.")
                self.ignoring_files.add(ftp_path)
            except Exception as e:
                console.print(f"[error]Sync failed for {ftp_path}: {e}[/]")

    def delete_remote(self, ftp_path):
        with self.lock:
            try:
                ftp = connect(self.cfg)
                ftp.delete(ftp_path)
                ftp.quit()
                ok(f"Deleted [red]{ftp_path}[/] from server.")
            except Exception as e:
                console.print(f"[error]Delete failed for {ftp_path}: {e}[/]")

    def ftp_mkdirs(self, ftp, path):
        parts = path.split("/")
        current = ""
        for part in parts:
            if not part: continue
            current += "/" + part
            try:
                ftp.mkd(current)
            except:
                pass

def start_watcher():
    if not os.path.exists(".crow-manifest.json"):
        console.print("[error]No manifest found. Run 'crow workspace init' first.[/]")
        return

    # Load CROW.md config
    crow_cfg = load_crow_md()
    auto_scan_paths = crow_cfg.get("auto_scan", [])
    scan_interval = crow_cfg.get("scan_interval", 5)

    manifest = Manifest()
    event_handler = CrowWatcherHandler(manifest)
    
    # Handle auto_yes from CROW.md
    if crow_cfg.get("auto_yes"):
        event_handler.always_yes_all = True
        info("Auto-Yes mode enabled via CROW.md")

    observer = Observer()
    observer.schedule(event_handler, path=".", recursive=True)
    
    console.print("[bold magenta]Crow Watching Agent Started[/]")
    
    if auto_scan_paths:
        console.print(f"[info]Auto-Scan enabled for {len(auto_scan_paths)} paths every {scan_interval}m[/]")
        # Start background thread for auto-scan
        scan_thread = threading.Thread(
            target=run_auto_scan, 
            args=(scan_interval, auto_scan_paths),
            daemon=True
        )
        scan_thread.start()

    console.print("[dim]Press Ctrl+C to stop[/]")
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        console.print("\n[info]Stopping Watcher...[/]")
    observer.join()
    ok("Watcher stopped.")
