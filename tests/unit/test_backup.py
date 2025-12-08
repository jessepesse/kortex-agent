"""
Unit tests for kortex/backup.py
"""

import pytest
import json
import zipfile
import io


class TestCreateBackup:
    """Tests for create_backup function"""
    
    def test_creates_valid_zip(self, temp_data_dir):
        """Should create a valid ZIP file"""
        from kortex.backup import create_backup
        from kortex.data import save_json_file
        
        # Create some data
        save_json_file("profile.json", {"name": "Test"})
        
        zip_bytes = create_backup()
        
        # Verify it's a valid ZIP
        buffer = io.BytesIO(zip_bytes)
        with zipfile.ZipFile(buffer, 'r') as zf:
            assert "manifest.json" in zf.namelist()
            assert "data/profile.json" in zf.namelist()
    
    def test_includes_manifest(self, temp_data_dir):
        """Should include manifest with correct structure"""
        from kortex.backup import create_backup
        from kortex.data import save_json_file
        
        save_json_file("profile.json", {"name": "Test"})
        
        zip_bytes = create_backup()
        
        buffer = io.BytesIO(zip_bytes)
        with zipfile.ZipFile(buffer, 'r') as zf:
            manifest = json.loads(zf.read("manifest.json"))
            
            assert "version" in manifest
            assert "created_at" in manifest
            assert "files" in manifest
            assert "stats" in manifest
    
    def test_selective_conversations(self, temp_data_dir):
        """Should include only selected conversations"""
        from kortex.backup import create_backup
        from kortex.data import save_conversation, generate_chat_id
        
        # Create conversations
        id1 = generate_chat_id()
        id2 = generate_chat_id()
        save_conversation(id1, [], "Chat 1")
        save_conversation(id2, [], "Chat 2")
        
        # Backup only first
        zip_bytes = create_backup(conversation_ids=[id1])
        
        buffer = io.BytesIO(zip_bytes)
        with zipfile.ZipFile(buffer, 'r') as zf:
            files = zf.namelist()
            assert f"conversations/{id1}.json" in files
            assert f"conversations/{id2}.json" not in files


class TestValidateBackup:
    """Tests for validate_backup function"""
    
    def test_valid_backup_passes(self, temp_data_dir):
        """Should validate a valid backup"""
        from kortex.backup import create_backup, validate_backup
        from kortex.data import save_json_file
        
        save_json_file("profile.json", {"name": "Test"})
        zip_bytes = create_backup()
        
        result = validate_backup(zip_bytes)
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
    
    def test_invalid_zip_fails(self):
        """Should fail for invalid ZIP"""
        from kortex.backup import validate_backup
        
        result = validate_backup(b"not a zip file")
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
    
    def test_missing_manifest_fails(self, temp_data_dir):
        """Should fail if manifest is missing"""
        from kortex.backup import validate_backup
        
        # Create ZIP without manifest
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zf:
            zf.writestr("data/test.json", '{"key": "value"}')
        
        result = validate_backup(buffer.getvalue())
        
        assert result["valid"] is False
        assert any("manifest" in e.lower() for e in result["errors"])


class TestRestoreBackup:
    """Tests for restore_backup function"""
    
    def test_restore_overwrites_data(self, temp_data_dir):
        """Should restore and overwrite existing data"""
        from kortex.backup import create_backup, restore_backup
        from kortex.data import save_json_file, load_json_file
        
        # Create original data
        save_json_file("profile.json", {"name": "Original"})
        
        # Create backup
        zip_bytes = create_backup()
        
        # Modify data
        save_json_file("profile.json", {"name": "Modified"})
        
        # Restore
        result = restore_backup(zip_bytes)
        
        assert result["success"] is True
        # Restore should bring back original
        restored = load_json_file("profile.json")
        assert restored["name"] == "Original"
    
    def test_restore_invalid_fails(self):
        """Should fail for invalid backup"""
        from kortex.backup import restore_backup
        
        result = restore_backup(b"not a zip")
        
        assert result["success"] is False


class TestGetBackupFilename:
    """Tests for get_backup_filename function"""
    
    def test_includes_timestamp(self):
        """Should include timestamp in filename"""
        from kortex.backup import get_backup_filename
        
        filename = get_backup_filename()
        
        assert filename.startswith("kortex_backup_")
        assert filename.endswith(".zip")
