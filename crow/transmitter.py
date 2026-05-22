import os
import struct
import secrets
import string
from pathlib import Path

def pack_folder(folder_path, output_path, callback=None):
    """
    Packs a folder into a custom binary stream format.
    Format: [4b path_len][path][8b data_len][data]
    All integers are Big-Endian.
    """
    all_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            all_files.append(os.path.join(root, file))
    
    with open(output_path, 'wb') as f_out:
        for abs_path in all_files:
            rel_path = os.path.relpath(abs_path, folder_path)
            # Use forward slashes for cross-platform compatibility
            rel_path = rel_path.replace(os.path.sep, '/')
            
            path_bytes = rel_path.encode('utf-8')
            path_len = len(path_bytes)
            file_size = os.path.getsize(abs_path)
            
            # [4 bytes path length] - Big Endian
            f_out.write(struct.pack(">I", path_len))
            f_out.write(path_bytes)
            # [8 bytes data length] - Big Endian
            f_out.write(struct.pack(">Q", file_size))
            
            with open(abs_path, 'rb') as f_in:
                while True:
                    chunk = f_in.read(1024 * 1024) # 1MB chunks for faster local packing
                    if not chunk:
                        break
                    f_out.write(chunk)
            
            if callback:
                callback(rel_path, file_size)

def generate_bridge(pack_name):
    key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    template_path = Path(__file__).parent / "bridge_template.php"
    with open(template_path, "r") as f:
        content = f.read()
    
    content = content.replace("{{KEY}}", key)
    content = content.replace("{{ZIP_NAME}}", pack_name)
    return content, key
