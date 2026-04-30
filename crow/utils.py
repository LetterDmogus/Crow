import sys

def die(msg: str, code: int = 1):
    print(f"[crow] ERROR: {msg}", file=sys.stderr)
    sys.exit(code)

def ok(msg: str):
    print(f"[crow] OK: {msg}")
