import json
import ftplib
from pathlib import Path
from crow.utils import die

CONFIG_FILENAME = ".ftp-tool.json"
SESSION_FILENAME = ".crow_sessions.json"

def find_config() -> Path:
    current = Path.cwd()
    for parent in [current, *current.parents]:
        candidate = parent / CONFIG_FILENAME
        if candidate.exists():
            return candidate
    return Path.home() / CONFIG_FILENAME

def load_config(config_path: Path = None) -> dict:
    path = config_path or find_config()
    if not path.exists():
        die(f"Config not found. Run: crow init")
    with open(path) as f:
        return json.load(f)

def save_config(data: dict, path: Path = None):
    target = path or (Path.cwd() / CONFIG_FILENAME)
    with open(target, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[crow] Config saved to {target}")

# ─── Session Management ────────────────────────────────────────────────────────

def load_sessions() -> dict:
    path = Path.cwd() / SESSION_FILENAME
    if not path.exists():
        return {"default": "/"}
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return {"default": "/"}

def save_sessions(sessions: dict):
    path = Path.cwd() / SESSION_FILENAME
    with open(path, "w") as f:
        json.dump(sessions, f, indent=2)

def get_cwd(session_id: str = "default") -> str:
    sessions = load_sessions()
    return sessions.get(session_id, "/")

def resolve_remote_path(path: str, session_id: str = "default") -> str:
    """Combine session CWD with requested path."""
    if not path:
        path = "."
        
    if path.startswith("/"):
        return path
    
    cwd = get_cwd(session_id).rstrip("/")
    if path == ".":
        return cwd if cwd else "/"
        
    return f"{cwd}/{path}"

def get_watchout_dir() -> Path:
    path = Path.cwd() / ".watchout"
    path.mkdir(exist_ok=True)
    return path

def load_watchout_config() -> dict:
    path = get_watchout_dir() / "config.json"
    default = {
        "conflict_detect": True,
        "large_file_warning": True,
        "sensitive_data_scan": True,
        "syntax_guard": True,
        "smart_context": True,
        "quota_watcher": True,
        "integrity_verify": True
    }
    if not path.exists():
        with open(path, "w") as f: json.dump(default, f, indent=2)
        return default
    try:
        with open(path) as f: return json.load(f)
    except: return default

def load_versions() -> dict:
    path = get_watchout_dir() / "versions.json"
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return {}

def save_versions(versions: dict):
    path = get_watchout_dir() / "versions.json"
    with open(path, "w") as f:
        json.dump(versions, f, indent=2)

def get_cwd(session_id: str = "default") -> str:
    sessions = load_sessions()
    return sessions.get(session_id, "/")

def resolve_remote_path(path: str, session_id: str = "default") -> str:
    """Combine session CWD with requested path."""
    if not path:
        path = "."
        
    if path.startswith("/"):
        return path
    
    cwd = get_cwd(session_id).rstrip("/")
    if path == ".":
        return cwd if cwd else "/"
        
    return f"{cwd}/{path}"

# ─── FTP Connection ─────────────────────────────────────────────────────────────

def connect(cfg: dict) -> ftplib.FTP:
    ftp = ftplib.FTP()
    host = cfg["host"]
    port = int(cfg.get("port", 21))
    timeout = int(cfg.get("timeout", 10))

    ftp.connect(host, port, timeout=timeout)
    ftp.login(cfg["user"], cfg["password"])

    passive = cfg.get("passive", True)
    ftp.set_pasv(passive)

    # Note: We don't automatically CWD here anymore, 
    # we handle it per command using resolve_remote_path
    return ftp
