import os
import json
import time
from pathlib import Path

CACHE_FILE = Path.cwd() / ".crow_cache.json"

def get_icon(name: str, is_dir: bool) -> str:
    """Return a fixed-width icon for layout stability."""
    if is_dir: return "dir "
    ext = os.path.splitext(name)[1].lower()
    if name == ".env": return "env "
    if name == ".htaccess": return "cfg "
    icons = {
        ".php": "php ", ".py": "py  ", ".md": "md  ", ".json": "json",
        ".sql": "sql ", ".js": "js  ", ".css": "css ", ".html": "html",
        ".jpg": "img ", ".png": "img ", ".zip": "zip ",
    }
    return icons.get(ext, "file")

def format_size(size_str: str) -> str:
    """Convert byte size string to human readable format (KB, MB, GB)."""
    try:
        size = int(size_str)
    except (ValueError, TypeError):
        return size_str  # Return original if not an int (e.g. empty or dir)

    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}" if unit != 'B' else f"{size} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"

def load_cache():
    if not CACHE_FILE.exists():
        return {"sessions": {}}
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"sessions": {}}

def save_cache(cache):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def get_cached_entries(session_id, path):
    cache = load_cache()
    session_cache = cache.get("sessions", {}).get(session_id, {})
    path_cache = session_cache.get("paths", {}).get(path)
    if path_cache:
        return path_cache.get("entries"), path_cache.get("last_refreshed")
    return None, None

def set_cached_entries(session_id, path, entries):
    cache = load_cache()
    if "sessions" not in cache: cache["sessions"] = {}
    if session_id not in cache["sessions"]: cache["sessions"][session_id] = {"paths": {}}
    
    last_refreshed = time.strftime("%Y-%m-%d %H:%M:%S")
    cache["sessions"][session_id]["paths"][path] = {
        "entries": entries,
        "last_refreshed": last_refreshed
    }
    save_cache(cache)
    return last_refreshed
