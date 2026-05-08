import os
import pytest
from crow.workspace import check_integrity, fix_integrity
from crow.manifest import Manifest

def test_check_integrity_all_missing(tmp_path):
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        results = check_integrity()
        assert results["manifest"] is False
        assert results["workspace"] is False
        assert results["crow_md"] is False
    finally:
        os.chdir(original_cwd)

def test_check_integrity_partial(tmp_path):
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        # Create manifest
        manifest = Manifest()
        manifest.save()
        
        # Create workspace dir
        os.makedirs("workspace")
        
        results = check_integrity()
        assert results["manifest"] is True
        assert results["workspace"] is True
        assert results["crow_md"] is False
    finally:
        os.chdir(original_cwd)

def test_check_integrity_crow_md_exists(tmp_path):
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        with open("CROW.md", "w") as f:
            f.write("config")
        
        results = check_integrity()
        assert results["crow_md"] is True
    finally:
        os.chdir(original_cwd)

def test_fix_integrity_missing_files_in_existing_workspace(tmp_path):
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        os.makedirs("workspace")
        with open("workspace/existing.txt", "w") as f:
            f.write("content")
            
        manifest = Manifest()
        manifest.set_file("existing.txt", status="synced")
        manifest.set_file("missing.txt", status="skeleton")
        manifest.save()
        
        fix_integrity()
        
        assert os.path.exists("workspace/existing.txt")
        assert os.path.exists("workspace/missing.txt")
        # Ensure existing file wasn't overwritten (though ghosting uses 'a' mode, it shouldn't truncate)
        with open("workspace/existing.txt", "r") as f:
            assert f.read() == "content"
    finally:
        os.chdir(original_cwd)

def test_fix_integrity_missing_workspace(tmp_path):
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        manifest = Manifest()
        manifest.set_file("test.txt", status="skeleton")
        manifest.save()
        
        # Workspace is missing
        assert not os.path.exists("workspace")
        
        fix_integrity()
        
        assert os.path.exists("workspace")
        assert os.path.exists("workspace/test.txt")
    finally:
        os.chdir(original_cwd)
