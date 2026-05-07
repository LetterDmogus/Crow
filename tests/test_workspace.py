import os
import pytest
from crow.workspace import create_ghost_file

def test_create_ghost_file(tmp_path):
    # Change to tmp_path to avoid creating files in the project root
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        file_path = "subdir/test.txt"
        create_ghost_file(file_path)
        
        full_path = tmp_path / file_path
        assert full_path.exists()
        assert full_path.is_file()
        assert full_path.stat().st_size == 0
    finally:
        os.chdir(original_cwd)
