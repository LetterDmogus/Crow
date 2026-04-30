import sys
import os
import ftplib
import tempfile
import json
import time
from pathlib import Path
from crow.core import connect, load_config, save_config, CONFIG_FILENAME
from crow.utils import ok, die
from crow.safeguards import make_backup, validate_action, backup_folder_local

def cmd_init(args):
    print("=== crow init ===")
    cfg = {}
    cfg["host"]     = input("FTP Host (e.g. ftp.example.com): ").strip()
    cfg["port"]     = int(input("Port [21]: ").strip() or "21")
    cfg["user"]     = input("Username: ").strip()
    cfg["password"] = input("Password: ").strip()
    cfg["base_dir"] = input("Base remote dir [/]: ").strip() or "/"
    passive_raw     = input("Passive mode? [Y/n]: ").strip().lower()
    cfg["passive"]  = passive_raw not in ("n", "no")

    print("\nTesting connection...")
    try:
        ftp = connect(cfg)
        print(f"  Connected. Current dir: {ftp.pwd()}")
        ftp.quit()
    except Exception as e:
        die(f"Connection failed: {e}")

    path = Path(args.config) if args.config else Path.cwd() / CONFIG_FILENAME
    save_config(cfg, path)
    print(f"\n[crow] Add {CONFIG_FILENAME} to .gitignore to protect credentials!")

def cmd_list(args):
    cfg = load_config()
    try:
        ftp = connect(cfg)
        target = args.path if args.path else ftp.pwd()
        entries = []
        ftp.retrlines(f"LIST {target}", entries.append)
        ftp.quit()
        for line in entries:
            print(line)
    except Exception as e:
        die(str(e))

def cmd_get(args):
    cfg = load_config()
    remote = args.remote
    local  = args.local or Path(remote).name
    try:
        ftp = connect(cfg)
        with open(local, "wb") as f:
            ftp.retrbinary(f"RETR {remote}", f.write)
        ftp.quit()
        ok(f"Downloaded {remote} → {local}")
    except Exception as e:
        die(str(e))

def cmd_put(args):
    cfg = load_config()
    local  = args.local
    remote = args.remote or ("/" + Path(local).name)
    if not Path(local).exists():
        die(f"Local file not found: {local}")
    try:
        ftp = connect(cfg)
        with open(local, "rb") as f:
            ftp.storbinary(f"STOR {remote}", f)
        ftp.quit()
        ok(f"Uploaded {local} → {remote}")
    except Exception as e:
        die(str(e))

def cmd_read(args):
    cfg = load_config()
    remote = args.remote
    try:
        ftp = connect(cfg)
        lines = []
        ftp.retrlines(f"RETR {remote}", lines.append)
        ftp.quit()
        print("\n".join(lines))
    except Exception as e:
        die(str(e))

def cmd_tail(args):
    """Read the last N lines of a remote file."""
    cfg = load_config()
    remote = args.remote
    lines_count = int(args.lines or 20)
    try:
        ftp = connect(cfg)
        size = ftp.size(remote)
        offset = max(0, size - (lines_count * 200))
        lines = []
        ftp.voidcmd(f"REST {offset}")
        ftp.retrlines(f"RETR {remote}", lines.append)
        ftp.quit()
        output = lines[-lines_count:]
        print("\n".join(output))
    except Exception as e:
        die(f"Tail failed (server might not support offset): {e}")

def cmd_write(args):
    cfg = load_config()
    remote  = args.remote
    content = args.content
    force   = getattr(args, "force", False)

    if content == "-":
        content = sys.stdin.read()

    validate_action(remote, content, force)

    try:
        ftp = connect(cfg)
        make_backup(ftp, remote)
        encoded = content.encode("utf-8")
        import io
        buf = io.BytesIO(encoded)
        ftp.storbinary(f"STOR {remote}", buf)
        ftp.quit()
        ok(f"Written {len(encoded)} bytes → {remote}")
    except Exception as e:
        die(str(e))

def cmd_delete(args):
    cfg = load_config()
    remote = args.remote
    force  = getattr(args, "force", False)

    validate_action(remote, None, force)

    try:
        ftp = connect(cfg)
        make_backup(ftp, remote)
        ftp.delete(remote)
        ftp.quit()
        ok(f"Deleted {remote} from server (backup saved locally)")
    except Exception as e:
        die(str(e))

def cmd_mkdir(args):
    cfg = load_config()
    remote = args.remote
    try:
        ftp = connect(cfg)
        ftp.mkd(remote)
        ftp.quit()
        ok(f"Created directory {remote}")
    except Exception as e:
        die(str(e))

def cmd_edit(args):
    cfg = load_config()
    remote = args.remote
    force  = getattr(args, "force", False)
    editor = os.environ.get("EDITOR", "nano")

    validate_action(remote, None, force)

    try:
        ftp = connect(cfg)
        suffix = Path(remote).suffix or ".txt"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name
            ftp.retrbinary(f"RETR {remote}", tmp.write)
        ftp.quit()

        os.system(f"{editor} {tmp_path}")

        with open(tmp_path, "r") as f:
            new_content = f.read()
        
        validate_action(remote, new_content, force)

        ftp2 = connect(cfg)
        make_backup(ftp2, remote)
        with open(tmp_path, "rb") as f:
            ftp2.storbinary(f"STOR {remote}", f)
        ftp2.quit()

        os.unlink(tmp_path)
        ok(f"Edited and re-uploaded {remote}")
    except Exception as e:
        die(str(e))

def cmd_info(args):
    cfg = load_config()
    safe = {k: v for k, v in cfg.items() if k != "password"}
    safe["password"] = "****"
    print(json.dumps(safe, indent=2))

def cmd_map(args):
    """Recursively map the FTP structure and sync with server cache."""
    cfg = load_config()
    cache_filename = ".crow_map.cache"
    tree_file = "FTP_TREE.md"
    refresh = getattr(args, "refresh", False)
    
    try:
        ftp = connect(cfg)
        if not refresh:
            try:
                print(f"[crow] Checking for remote cache {cache_filename}...")
                lines = []
                ftp.retrlines(f"RETR {cache_filename}", lines.append)
                with open(tree_file, "w") as f:
                    f.write("\n".join(lines))
                ok(f"Synced from server cache. See {tree_file}")
                ftp.quit()
                return
            except ftplib.error_perm:
                print("[crow] No remote cache found. Starting full scan...")
        else:
            print("[crow] Refresh forced. Starting full scan...")

        ignore_dirs = ["vendor", "node_modules", ".git", "storage", "cache", ".crow_backups"]
        tree_lines = ["# FTP Project Tree", f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}", ""]
        
        def walk(path, depth=0):
            prefix = "  " * depth + "├── "
            try:
                items = []
                ftp.retrlines(f"LIST {path}", items.append)
                for item in items:
                    parts = item.split()
                    name = parts[-1]
                    if name in [".", ".."]: continue
                    is_dir = item.startswith("d")
                    tree_lines.append(f"{prefix}{name}{'/' if is_dir else ''}")
                    if is_dir and name not in ignore_dirs and depth < 5:
                        walk(f"{path.rstrip('/')}/{name}", depth + 1)
            except Exception as e:
                tree_lines.append(f"{prefix}[Error accessing {path}: {e}]")

        walk("/")
        content = "\n".join(tree_lines)
        with open(tree_file, "w") as f:
            f.write(content)
        
        import io
        buf = io.BytesIO(content.encode("utf-8"))
        ftp.storbinary(f"STOR {cache_filename}", buf)
        ftp.quit()
        ok(f"FTP mapped and cache uploaded to server as {cache_filename}")
    except Exception as e:
        die(str(e))

def cmd_pull(args):
    """Download a remote directory to local path recursively."""
    cfg = load_config()
    remote_dir = args.remote
    local_dir  = args.local or Path(remote_dir).name
    
    backup_folder_local(local_dir)

    try:
        ftp = connect(cfg)
        def pull_recursive(rem_path, loc_path):
            Path(loc_path).mkdir(parents=True, exist_ok=True)
            items = []
            ftp.retrlines(f"LIST {rem_path}", items.append)
            for item in items:
                parts = item.split()
                name = parts[-1]
                if name in [".", ".."]: continue
                
                if name in ["vendor", "node_modules", ".git", ".crow_backups", "storage", "cache"]:
                    continue

                r_item = f"{rem_path.rstrip('/')}/{name}"
                l_item = Path(loc_path) / name
                if item.startswith("d"):
                    pull_recursive(r_item, l_item)
                else:
                    with open(l_item, "wb") as f:
                        ftp.retrbinary(f"RETR {r_item}", f.write)
                    print(f"  [pull] {r_item} -> {l_item}")
        pull_recursive(remote_dir, local_dir)
        ftp.quit()
        ok(f"Pull completed: {remote_dir} -> {local_dir}")
    except Exception as e:
        die(str(e))

def cmd_push(args):
    """Upload a local directory to remote path recursively."""
    cfg = load_config()
    local_dir  = args.local
    remote_dir = args.remote or ("/" + Path(local_dir).name)
    if not Path(local_dir).exists():
        die(f"Local directory not found: {local_dir}")

    try:
        ftp = connect(cfg)
        def push_recursive(loc_path, rem_path):
            try:
                ftp.mkd(rem_path)
            except:
                pass
            for item in os.listdir(loc_path):
                l_item = Path(loc_path) / item
                r_item = f"{rem_path.rstrip('/')}/{item}"
                if l_item.is_dir():
                    if item in ["vendor", "node_modules", ".git", ".crow_backups"]:
                        continue
                    push_recursive(l_item, r_item)
                else:
                    make_backup(ftp, r_item)
                    with open(l_item, "rb") as f:
                        ftp.storbinary(f"STOR {r_item}", f)
                    print(f"  [push] {l_item} -> {r_item}")
        push_recursive(local_dir, remote_dir)
        ftp.quit()
        ok(f"Push completed: {local_dir} -> {remote_dir}")
    except Exception as e:
        die(str(e))
