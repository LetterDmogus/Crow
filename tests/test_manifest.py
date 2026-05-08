import os
import json
import pytest
from crow.manifest import Manifest

def test_manifest_init_new(tmp_path):
    manifest_path = tmp_path / ".crow-manifest.json"
    manifest = Manifest(str(manifest_path))
    
    assert manifest.path == str(manifest_path)
    assert manifest.data["version"] == "2.0.1"
    assert manifest.data["files"] == {}

def test_manifest_save_load(tmp_path):
    manifest_path = tmp_path / ".crow-manifest.json"
    manifest = Manifest(str(manifest_path))
    manifest.set_file("test.txt", "synced", 1234.5, "abc")
    manifest.save()
    
    assert os.path.exists(manifest_path)
    
    # Load in new instance
    new_manifest = Manifest(str(manifest_path))
    assert new_manifest.data["files"]["test.txt"]["status"] == "synced"
    assert new_manifest.data["files"]["test.txt"]["remote_mtime"] == 1234.5
    assert new_manifest.data["files"]["test.txt"]["checksum"] == "abc"

def test_manifest_set_file_updates_existing(tmp_path):
    manifest_path = tmp_path / ".crow-manifest.json"
    manifest = Manifest(str(manifest_path))
    manifest.set_file("test.txt", "synced", 1234.5, "abc")
    manifest.set_file("test.txt", "modified", 1234.6, "def")
    
    assert manifest.data["files"]["test.txt"]["status"] == "modified"
    assert manifest.data["files"]["test.txt"]["remote_mtime"] == 1234.6
    assert manifest.data["files"]["test.txt"]["checksum"] == "def"
