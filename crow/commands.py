import sys
import os
import ftplib
import tempfile
import json
import time
import subprocess
import re
from pathlib import Path
from rich.table import Table
from rich.markdown import Markdown
from crow.core import connect, load_config, save_config, CONFIG_FILENAME, load_sessions, save_sessions, resolve_remote_path, get_cwd
from crow.utils import ok, die, console, info
from crow.safeguards import make_backup, validate_action, backup_folder_local

def parse_ftp_line(line: str):
    """Robust parser for FTP LIST output."""
    parts = line.split()
    if not parts or len(parts) < 3: return None
    
    # Name is usually the last part, but can contain spaces
    # A safer way for most Unix-style FTPs:
    # 0:perms, 1:links, 2:owner, 3:group, 4:size, 5:month, 6:day, 7:time/year, 8+:name
    name = " ".join(parts[8:]) if len(parts) >= 9 else parts[-1]
    
    if name in [".", ".."]: return None
    
    is_dir = line.lower().startswith("d")
    size = parts[4] if len(parts) >= 5 else "0"
    modified = " ".join(parts[5:8]) if len(parts) >= 8 else ""
    
    return {
        "name": name,
        "is_dir": is_dir,
        "size": size,
        "modified": modified
    }

def smart_resolve(ftp: ftplib.FTP, remote_path: str) -> str:
    """If file doesn't exist, try to find a file with extensions starting with this name."""
    try:
        ftp.size(remote_path)
        return remote_path
    except:
        pass

    parent = os.path.dirname(remote_path) or "."
    basename = os.path.basename(remote_path)
    
    try:
        items = []
        ftp.retrlines(f"LIST {parent}", items.append)
        for line in items:
            item = parse_ftp_line(line)
            if not item: continue
            
            if item["name"].startswith(basename + "."):
                resolved = f"{parent.rstrip('/')}/{item['name']}".replace("./", "")
                console.print(f"[dim][crow] Smart lookup: resolved [cyan]{basename}[/] to [green]{item['name']}[/][/]")
                return resolved
    except:
        pass
    
    return remote_path

def cmd_init(args):
    console.print("[bold magenta]=== Crow Init ===[/]")
    cfg = {}
    cfg["host"]     = input("FTP Host (e.g. ftp.example.com): ").strip()
    cfg["port"]     = int(input("Port [21]: ").strip() or "21")
    cfg["user"]     = input("Username: ").strip()
    cfg["password"] = input("Password: ").strip()
    cfg["base_dir"] = input("Base remote dir [/]: ").strip() or "/"
    passive_raw     = input("Passive mode? [Y/n]: ").strip().lower()
    cfg["passive"]  = passive_raw not in ("n", "no")
    console.print("\n[info]Testing connection...[/]")
    try:
        ftp = connect(cfg); ok(f"Connected. Current dir: {ftp.pwd()}"); ftp.quit()
    except Exception as e: die(f"Connection failed: {e}")
    path = Path(args.config) if args.config else Path.cwd() / CONFIG_FILENAME
    save_config(cfg, path)
    console.print(f"\n[warning]Add {CONFIG_FILENAME} to .gitignore to protect credentials![/]")

def cmd_skill(args):
    skill_path = Path(__file__).parent.parent / "SKILL.md"
    if not skill_path.exists(): die("SKILL.md not found.")
    with open(skill_path, "r") as f: console.print(Markdown(f.read()))

def cmd_cd(args):
    session_id = args.id or "default"; path = args.path
    sessions = load_sessions(); new_path = resolve_remote_path(path, session_id)
    if new_path != "/" and new_path.endswith("/"): new_path = new_path.rstrip("/")
    sessions[session_id] = new_path; save_sessions(sessions)
    ok(f"Session [session]'{session_id}'[/] CWD: [cyan]{new_path}[/]")

def cmd_list(args):
    cfg = load_config(); session_id = getattr(args, "id", "default")
    target = resolve_remote_path(args.path, session_id)
    try:
        ftp = connect(cfg); entries = []; ftp.retrlines(f"LIST {target}", entries.append); ftp.quit()
        console.print(f"[info]Listing:[/] [bold cyan]{target}[/]")
        for line in entries:
            item = parse_ftp_line(line)
            if not item: continue
            style = "green" if item["is_dir"] else "white"
            console.print(f"[{style}]{line}[/]")
    except Exception as e: die(str(e))

def get_remote_content(args) -> str:
    cfg = load_config(); session_id = getattr(args, "id", "default")
    remote = resolve_remote_path(args.remote, session_id)
    try:
        ftp = connect(cfg); remote = smart_resolve(ftp, remote)
        lines = []; ftp.retrlines(f"RETR {remote}", lines.append); ftp.quit()
        return "\n".join(lines)
    except Exception as e:
        console.print(f"[error]Read Error:[/] {e}"); return None

def cmd_read(args):
    content = get_remote_content(args)
    if content: print(content)

def cmd_get(args):
    cfg = load_config(); session_id = getattr(args, "id", "default")
    remote = resolve_remote_path(args.remote, session_id); local = args.local or Path(remote).name
    try:
        ftp = connect(cfg); remote = smart_resolve(ftp, remote)
        with open(local, "wb") as f: ftp.retrbinary(f"RETR {remote}", f.write)
        ftp.quit(); ok(f"Downloaded [cyan]{remote}[/] → [green]{local}[/]")
    except Exception as e: die(str(e))

def cmd_put(args):
    cfg = load_config(); session_id = getattr(args, "id", "default")
    local = args.local; remote = resolve_remote_path(args.remote, session_id)
    if not Path(local).exists(): die(f"Local file not found: {local}")
    with open(local, "r") as f: content = f.read()
    validate_action(remote, content, getattr(args, "force", False))
    try:
        ftp = connect(cfg); make_backup(ftp, remote)
        with open(local, "rb") as f: ftp.storbinary(f"STOR {remote}", f)
        ftp.quit(); ok(f"Uploaded [green]{local}[/] → [cyan]{remote}[/]")
    except Exception as e: die(str(e))

def cmd_tail(args):
    cfg = load_config(); session_id = getattr(args, "id", "default")
    remote = resolve_remote_path(args.remote, session_id); lines_count = int(args.lines or 20)
    try:
        ftp = connect(cfg); remote = smart_resolve(ftp, remote); size = ftp.size(remote)
        offset = max(0, size - (lines_count * 200)); lines = []
        ftp.voidcmd(f"REST {offset}"); ftp.retrlines(f"RETR {remote}", lines.append); ftp.quit()
        output = lines[-lines_count:]
        console.print(f"[info]Last {len(output)} lines of {remote}:[/]")
        for l in output: console.print(l)
    except Exception as e: die(f"Tail failed: {e}")

def cmd_write(args):
    cfg = load_config(); session_id = getattr(args, "id", "default")
    remote = resolve_remote_path(args.remote, session_id); content = args.content
    force = getattr(args, "force", False)
    if content == "-": content = sys.stdin.read()
    validate_action(remote, content, force)
    try:
        ftp = connect(cfg); make_backup(ftp, remote); encoded = content.encode("utf-8")
        import io; buf = io.BytesIO(encoded); ftp.storbinary(f"STOR {remote}", buf); ftp.quit()
        ok(f"Written {len(encoded)} bytes → [cyan]{remote}[/]")
    except Exception as e: die(str(e))

def cmd_delete(args):
    cfg = load_config(); session_id = getattr(args, "id", "default")
    remote = resolve_remote_path(args.remote, session_id); force = getattr(args, "force", False)
    try:
        ftp = connect(cfg); remote = smart_resolve(ftp, remote)
        validate_action(remote, None, force); make_backup(ftp, remote)
        ftp.delete(remote); ftp.quit(); ok(f"Deleted [cyan]{remote}[/] (Backup saved locally)")
    except Exception as e: die(str(e))

def cmd_mkdir(args):
    cfg = load_config(); session_id = getattr(args, "id", "default")
    remote = resolve_remote_path(args.remote, session_id)
    try:
        ftp = connect(cfg); ftp.mkd(remote); ftp.quit()
        ok(f"Created directory [cyan]{remote}[/]")
    except Exception as e: die(str(e))

def cmd_edit(args):
    cfg = load_config(); session_id = getattr(args, "id", "default")
    remote = resolve_remote_path(args.remote, session_id); force = getattr(args, "force", False)
    path_only = getattr(args, "path_only", False); editor = os.environ.get("EDITOR", "nano")
    try:
        ftp = connect(cfg); remote = smart_resolve(ftp, remote); validate_action(remote, None, force)
        suffix = Path(remote).suffix or ".txt"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name; ftp.retrbinary(f"RETR {remote}", tmp.write)
        ftp.quit()
        if path_only: console.print(f"[success]File downloaded.[/]"); print(tmp_path); return
        console.print(f"[info]Opening {editor}...[/]"); os.system(f"{editor} {tmp_path}")
        with open(tmp_path, "r") as f: new_content = f.read()
        validate_action(remote, new_content, force); ftp2 = connect(cfg); make_backup(ftp2, remote)
        with open(tmp_path, "rb") as f: ftp2.storbinary(f"STOR {remote}", f)
        ftp2.quit(); os.unlink(tmp_path); ok(f"Edited and re-uploaded [cyan]{remote}[/]")
    except Exception as e: die(str(e))

def cmd_info(args):
    cfg = load_config(); session_id = getattr(args, "id", "default")
    table = Table(title="Crow Configuration", show_header=False, box=None)
    table.add_column("Key", style="bold cyan"); table.add_column("Value", style="white")
    for k, v in cfg.items():
        val = "****" if k == "password" else str(v)
        table.add_row(k.replace("_", " ").title(), val)
    table.add_row("Session ID", session_id); table.add_row("Virtual CWD", get_cwd(session_id))
    console.print(table)

def cmd_shell(args):
    from crow.shell import CrowShell; shell = CrowShell(); shell.cmdloop()

def cmd_browse(args):
    from crow.tui.app import CrowBrowser; app = CrowBrowser(); app.run()

def cmd_map(args):
    cfg = load_config(); cache_filename = ".crow_map.cache"; tree_file = "FTP_TREE.md"
    refresh = getattr(args, "refresh", False)
    try:
        ftp = connect(cfg)
        if not refresh:
            try:
                info(f"Checking for remote cache [cyan]{cache_filename}[/]...")
                lines = []; ftp.retrlines(f"RETR {cache_filename}", lines.append)
                with open(tree_file, "w") as f: f.write("\n".join(lines))
                ok(f"Synced from server cache. See [green]{tree_file}[/]"); ftp.quit(); return
            except ftplib.error_perm: info("No remote cache found. Starting full scan...")
        else: info("Refresh forced. Starting full scan...")

        ignore_dirs = ["vendor", "node_modules", ".git", "storage", "cache", ".crow_backups"]
        tree_lines = ["# FTP Project Tree", f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}", ""]
        def walk(path, depth=0):
            prefix = "  " * depth + "├── "; items = []
            try:
                ftp.retrlines(f"LIST {path}", items.append)
                for line in items:
                    item = parse_ftp_line(line)
                    if not item: continue
                    tree_lines.append(f"{prefix}{item['name']}{'/' if item['is_dir'] else ''}")
                    if item['is_dir'] and item['name'] not in ignore_dirs and depth < 5:
                        walk(f"{path.rstrip('/')}/{item['name']}", depth + 1)
            except: pass
        walk("/"); content = "\n".join(tree_lines)
        with open(tree_file, "w") as f: f.write(content)
        import io; buf = io.BytesIO(content.encode("utf-8")); ftp.storbinary(f"STOR {cache_filename}", buf)
        ftp.quit(); ok(f"FTP mapped and cache uploaded.")
    except Exception as e: die(str(e))

def cmd_pull(args):
    cfg = load_config(); session_id = getattr(args, "id", "default")
    remote_dir = resolve_remote_path(args.remote, session_id); local_dir = args.local or Path(remote_dir).name
    backup_folder_local(local_dir)
    try:
        ftp = connect(cfg)
        def pull_recursive(rem_path, loc_path):
            Path(loc_path).mkdir(parents=True, exist_ok=True); items = []
            ftp.retrlines(f"LIST {rem_path}", items.append)
            for line in items:
                item = parse_ftp_line(line)
                if not item or item["name"] in ["vendor", "node_modules", ".git", ".crow_backups", "storage", "cache"]: continue
                r_item = f"{rem_path.rstrip('/')}/{item['name']}"; l_item = Path(loc_path) / item['name']
                if item['is_dir']: pull_recursive(r_item, l_item)
                else:
                    with open(l_item, "wb") as f: ftp.retrbinary(f"RETR {r_item}", f.write)
                    console.print(f"  [cyan]Pull:[/] {r_item} -> {l_item}")
        pull_recursive(remote_dir, local_dir); ftp.quit(); ok(f"Pull completed.")
    except Exception as e: die(str(e))

def cmd_push(args):
    cfg = load_config(); session_id = getattr(args, "id", "default")
    local_dir = args.local; remote_dir = resolve_remote_path(args.remote, session_id)
    if not Path(local_dir).exists(): die(f"Local directory not found.")
    try:
        ftp = connect(cfg)
        def push_recursive(loc_path, rem_path):
            try: ftp.mkd(rem_path)
            except: pass
            for item in os.listdir(loc_path):
                l_item = Path(loc_path) / item; r_item = f"{rem_path.rstrip('/')}/{item}"
                if l_item.is_dir():
                    if item in ["vendor", "node_modules", ".git", ".crow_backups"]: continue
                    push_recursive(l_item, r_item)
                else:
                    make_backup(ftp, r_item)
                    with open(l_item, "rb") as f: ftp.storbinary(f"STOR {r_item}", f)
                    console.print(f"  [green]Push:[/] {l_item} -> {r_item}")
        push_recursive(local_dir, remote_dir); ftp.quit(); ok(f"Push completed.")
    except Exception as e: die(str(e))

def cmd_diff(args):
    remote_content = get_remote_content(args)
    if not remote_content: return
    local_path = args.local
    if not Path(local_path).exists(): die(f"Local file not found.")
    with open(local_path, "r") as f: local_content = f.read()
    import difflib
    diff = difflib.unified_diff(remote_content.splitlines(), local_content.splitlines(), fromfile=f"remote:{args.remote}", tofile=f"local:{local_path}", lineterm="")
    for line in diff:
        if line.startswith('+'): console.print(f"[green]{line}[/]")
        elif line.startswith('-'): console.print(f"[red]{line}[/]")
        else: console.print(line)

def cmd_logs(args):
    cfg = load_config(); session_id = getattr(args, "id", "default")
    common_logs = ["error_log", "error.log", "storage/logs/laravel.log", "hai/storage/logs/laravel.log", "js/error_log"]
    try:
        ftp = connect(cfg); found = []
        for log_path in common_logs:
            try:
                full_path = log_path if log_path.startswith("/") else f"/{log_path}"
                ftp.size(full_path); found.append(full_path)
            except: continue
        if not found: info("No logs found."); return
        table = Table(title="Discovered Logs")
        table.add_column("ID", style="cyan"); table.add_column("Path", style="green")
        for i, path in enumerate(found): table.add_row(str(i+1), path)
        console.print(table)
        if args.tail:
            target = found[0]; ftp.quit(); cmd_tail(SimpleNamespace(id=session_id, remote=target, lines=20))
        else: ftp.quit()
    except Exception as e: die(str(e))

def cmd_search(args):
    pattern = args.pattern; session_id = getattr(args, "id", "default")
    if not args.content:
        tree_file = Path.cwd() / "FTP_TREE.md"
        if not tree_file.exists(): die("Run 'crow map' first.")
        info(f"Searching for '[bold cyan]{pattern}[/]'...")
        with open(tree_file, "r") as f:
            for line in f:
                if re.search(pattern, line, re.IGNORECASE): console.print(line.strip())
    else:
        cfg = load_config(); remote_path = resolve_remote_path(args.path or ".", session_id)
        info(f"Searching content in [green]{remote_path}[/]...")
        try:
            ftp = connect(cfg)
            def search_recursive(path):
                items = []; ftp.retrlines(f"LIST {path}", items.append)
                for line in items:
                    item = parse_ftp_line(line)
                    if not item: continue
                    full_p = f"{path.rstrip('/')}/{item['name']}"
                    if item["is_dir"]: search_recursive(full_p)
                    else:
                        try:
                            if int(item["size"]) > 500000: continue
                            lines = []; ftp.retrlines(f"RETR {full_p}", lines.append)
                            for i, l in enumerate(lines):
                                if pattern.lower() in l.lower(): console.print(f"[green]{full_p}:{i+1}:[/] {l.strip()}")
                        except: pass
            search_recursive(remote_path); ftp.quit()
        except Exception as e: die(str(e))
