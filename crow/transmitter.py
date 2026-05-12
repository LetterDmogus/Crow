import zipfile
import os
from pathlib import Path
import secrets
import string

def zip_folder(folder_path, output_path):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), folder_path)
                zipf.write(os.path.join(root, file), rel_path)

def generate_bridge(zip_name):
    key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    template_path = Path(__file__).parent / "bridge_template.php"
    with open(template_path, "r") as f:
        content = f.read()
    
    content = content.replace("{{KEY}}", key)
    content = content.replace("{{ZIP_NAME}}", zip_name)
    return content, key
