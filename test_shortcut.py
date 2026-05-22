from crow.workspace import generate_shortcut
import os
import sys

generate_shortcut()
if sys.platform.startswith("win"):
    path = "Crow Dashboard.bat"
else:
    path = "crow-dashboard.sh"

if os.path.exists(path):
    print(f"SUCCESS: {path} created.")
    with open(path, "r") as f:
        print("Content:")
        print(f.read())
else:
    print(f"FAILURE: {path} NOT created.")
