import json
import ftplib
from pathlib import Path
from crow.utils import die

CONFIG_FILENAME = ".ftp-tool.json"

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

def connect(cfg: dict) -> ftplib.FTP:
    ftp = ftplib.FTP()
    host = cfg["host"]
    port = int(cfg.get("port", 21))
    timeout = int(cfg.get("timeout", 10))

    ftp.connect(host, port, timeout=timeout)
    ftp.login(cfg["user"], cfg["password"])

    passive = cfg.get("passive", True)
    ftp.set_pasv(passive)

    base_dir = cfg.get("base_dir", "/")
    if base_dir and base_dir != "/":
        ftp.cwd(base_dir)

    return ftp
