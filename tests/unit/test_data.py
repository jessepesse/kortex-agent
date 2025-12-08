"""
Unit tests for kortex/data.py
"""

import pytest
import json
from pathlib import Path


class TestLoadJsonFile:
    """Tests for load_json_file function"""
    
    def test_load_existing_file(self, temp_data_dir, sample_profile_data):
        """Should load existing JSON file"""
        from kortex.data import load_json_file, save_json_file
        
        # Create test file
        save_json_file("profile.json", sample_profile_data)
        
        # Load and verify
        result = load_json_file("profile.json")
        assert result == sample_profile_data
    
    def test_load_nonexistent_creates_default(self, temp_data_dir):
        """Should create file with default data if not exists"""
        from kortex.data import load_json_file, DEFAULT_DATA
        
        result = load_json_file("profile.json")
        assert result == DEFAULT_DATA.get("profile", {})
    
    def test_load_corrupt_json_returns_default(self, temp_data_dir):
        """Should return default data for corrupt JSON"""
        from kortex.data import load_json_file, DEFAULT_DATA
        
        # Create corrupt file
        corrupt_file = temp_data_dir / "profile.json"
        corrupt_file.write_text("{ this is not valid json }")
        
        result = load_json_file("profile.json")
        assert result == DEFAULT_DATA.get("profile", {})


class TestSaveJsonFile:
    """Tests for save_json_file function"""
    
    def test_save_and_load(self, temp_data_dir, sample_profile_data):
        """Should save and load data correctly"""
        from kortex.data import save_json_file, load_json_file
        
        result = save_json_file("test.json", sample_profile_data)
        assert "Updated" in result or "✓" in result
        
        loaded = load_json_file("test.json")
        assert loaded == sample_profile_data
    
    def test_save_creates_directory(self, temp_data_dir):
        """Should create data directory if not exists"""
        from kortex.data import save_json_file
        import shutil
        
        # Remove data dir
        shutil.rmtree(temp_data_dir)
        
        # Save should recreate it
        save_json_file("test.json", {"key": "value"})
        assert temp_data_dir.exists()


class TestGetAllJsonFiles:
    """Tests for get_all_json_files function"""
    
    def test_returns_empty_for_empty_dir(self, temp_data_dir):
        """Should return empty list for empty directory"""
        from kortex.data import get_all_json_files
        
        result = get_all_json_files()
        assert result == []
    
    def test_returns_all_json_files(self, temp_data_dir):
        """Should return all JSON files in directory"""
        from kortex.data import get_all_json_files, save_json_file
        
        save_json_file("profile.json", {})
        save_json_file("health.json", {})
        save_json_file("values.json", {})
        
        result = get_all_json_files()
        assert len(result) == 3
        assert "profile.json" in result
        assert "health.json" in result


class TestLoadAllContext:
    """Tests for load_all_context function"""
    
    def test_initializes_default_data_if_empty(self, temp_data_dir):
        """Should initialize default data files if directory is empty"""
        from kortex.data import load_all_context, DEFAULT_DATA
        
        context = load_all_context()
        
        # Should have created default files
        assert "profile" in context
        assert "health" in context
    
    def test_loads_all_existing_files(self, temp_data_dir, sample_profile_data, sample_health_data):
        """Should load all existing JSON files"""
        from kortex.data import load_all_context, save_json_file
        
        save_json_file("profile.json", sample_profile_data)
        save_json_file("health.json", sample_health_data)
        
        context = load_all_context()
        
        assert context["profile"] == sample_profile_data
        assert context["health"] == sample_health_data


class TestConversationOperations:
    """Tests for conversation CRUD operations"""
    
    def test_generate_chat_id(self):
        """Should generate unique chat IDs"""
        from kortex.data import generate_chat_id
        
        id1 = generate_chat_id()
        id2 = generate_chat_id()
        
        assert id1 != id2
        assert "_" in id1  # Format: timestamp_uuid
    
    def test_save_and_load_conversation(self, temp_data_dir):
        """Should save and load conversation"""
        from kortex.data import save_conversation, load_conversation, generate_chat_id
        
        chat_id = generate_chat_id()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        save_conversation(chat_id, messages, "Test Chat")
        
        loaded = load_conversation(chat_id)
        assert loaded is not None
        assert loaded["title"] == "Test Chat"
        assert len(loaded["messages"]) == 2
    
    def test_list_conversations(self, temp_data_dir):
        """Should list all conversations"""
        from kortex.data import save_conversation, list_conversations, generate_chat_id
        
        # Create multiple conversations
        for i in range(3):
            chat_id = generate_chat_id()
            save_conversation(chat_id, [], f"Chat {i}")
        
        conversations = list_conversations()
        assert len(conversations) == 3
    
    def test_delete_conversation(self, temp_data_dir):
        """Should delete conversation"""
        from kortex.data import save_conversation, delete_conversation, load_conversation, generate_chat_id
        
        chat_id = generate_chat_id()
        save_conversation(chat_id, [], "To Delete")
        
        assert load_conversation(chat_id) is not None
        
        result = delete_conversation(chat_id)
        assert result is True
        
        assert load_conversation(chat_id) is None
    
    def test_toggle_pin(self, temp_data_dir):
        """Should toggle pin status"""
        from kortex.data import save_conversation, toggle_pin, load_conversation, generate_chat_id
        
        chat_id = generate_chat_id()
        save_conversation(chat_id, [], "Pinnable")
        
        # Initially not pinned
        conv = load_conversation(chat_id)
        assert conv["pinned"] is False
        
        # Toggle to pinned
        result = toggle_pin(chat_id)
        assert result is True
        
        # Verify
        conv = load_conversation(chat_id)
        assert conv["pinned"] is True
