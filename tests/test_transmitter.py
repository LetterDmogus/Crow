import os
import zipfile
from crow.transmitter import zip_folder

def test_zip_folder(tmp_path):
    d = tmp_path / "src"
    d.mkdir()
    (d / "hello.txt").write_text("world")
    
    zip_path = tmp_path / "output.zip"
    zip_folder(str(d), str(zip_path))
    
    assert zip_path.exists()
    with zipfile.ZipFile(zip_path, 'r') as z:
        assert "hello.txt" in z.namelist()

def test_generate_bridge(tmp_path):
    from crow.transmitter import generate_bridge
    
    # Mock bridge_template.php content if needed, but it should exist in crow/
    # We can just check if it returns a string and a key
    content, key = generate_bridge("test.zip")
    
    assert isinstance(content, str)
    assert len(key) == 32
    assert key in content
    assert "test.zip" in content
