import json
import os
from typing import Dict, Any

class Manifest:
    def __init__(self, path: str = ".crow-manifest.json"):
        self.path = self._find_manifest(path)
        self.data = {"version": "2.0.1", "files": {}}
        if os.path.exists(self.path):
            self.load()

    def _find_manifest(self, filename):
        curr = os.getcwd()
        while True:
            target = os.path.join(curr, filename)
            if os.path.exists(target):
                return target
            parent = os.path.dirname(curr)
            if parent == curr: # Root reached
                return os.path.join(os.getcwd(), filename)
            curr = parent

    def load(self):
        with open(self.path, 'r') as f:
            self.data = json.load(f)

    def save(self):
        with open(self.path, 'w') as f:
            json.dump(self.data, f, indent=2)

    def set_file(self, path: str, status: str, remote_mtime: float = 0, checksum: str = ""):
        self.data["files"][path] = {
            "status": status,
            "remote_mtime": remote_mtime,
            "checksum": checksum
        }
