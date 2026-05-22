import os
import yaml
import re
from crow.manifest import Manifest

def load_crow_md():
    manifest = Manifest()
    root_dir = os.path.dirname(manifest.path)
    crow_path = os.path.join(root_dir, "CROW.md")
    
    default_config = {
        "auto_scan": [],
        "scan_interval": 5,
        "auto_yes": False
    }
    
    if not os.path.exists(crow_path):
        return default_config
        
    try:
        with open(crow_path, "r") as f:
            content = f.read()
            
        # Extract YAML frontmatter
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if match:
            yaml_content = match.group(1)
            user_config = yaml.safe_load(yaml_content)
            if user_config and isinstance(user_config, dict):
                return {**default_config, **user_config}
    except Exception:
        pass
        
    return default_config
