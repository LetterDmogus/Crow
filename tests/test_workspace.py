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

from crow.workspace import init_workspace
from crow.manifest import Manifest

def test_init_workspace_laravel(tmp_path):
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        remote_files = [
            "app/Models/User.php",
            "vendor/autoload.php",
            "node_modules/vue/package.json",
            "storage/logs/laravel.log",
            ".git/config",
            "public/index.php"
        ]
        
        init_workspace(remote_files, preset='laravel')
        
        assert os.path.exists("workspace/app/Models/User.php")
        assert os.path.exists("workspace/public/index.php")
        assert not os.path.exists("workspace/vendor/autoload.php")
        assert not os.path.exists("workspace/node_modules/vue/package.json")
        assert not os.path.exists("workspace/storage/logs/laravel.log")
        assert not os.path.exists("workspace/.git/config")
        
        manifest = Manifest()
        assert "app/Models/User.php" in manifest.data["files"]
        assert manifest.data["files"]["app/Models/User.php"]["status"] == "skeleton"
    finally:
        os.chdir(original_cwd)
