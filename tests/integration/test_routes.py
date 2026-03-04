"""
Integration tests for Flask API routes
"""

import pytest
import json
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def client(temp_data_dir, temp_config_file):
    """Create Flask test client with temp directories."""
    from backend.app import create_app
    
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client


class TestDataEndpoints:
    """Tests for /api/data/* endpoints"""
    
    def test_get_all_data(self, client, temp_data_dir):
        """GET /api/data should return all data files"""
        from kortex.data import save_json_file
        
        save_json_file("profile.json", {"name": "Test"})
        
        response = client.get('/api/data')
        
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["success"] is True
        assert "profile" in payload["data"]
    
    def test_get_specific_file(self, client, temp_data_dir):
        """GET /api/data/<filename> should return specific file"""
        from kortex.data import save_json_file
        
        save_json_file("health.json", {"energy": 8})
        
        response = client.get('/api/data/health')
        
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["success"] is True
        assert payload["data"]["energy"] == 8
    
    def test_update_data_file(self, client, temp_data_dir):
        """PUT /api/data/<filename> should update file"""
        from kortex.data import save_json_file, load_json_file
        
        save_json_file("profile.json", {"name": "Old"})
        
        response = client.put(
            '/api/data/profile',
            json={"data": {"name": "New", "location": "Helsinki"}}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        
        # Verify update
        profile = load_json_file("profile.json")
        assert profile["name"] == "New"


class TestHistoryEndpoints:
    """Tests for /api/history endpoints"""
    
    def test_get_empty_history(self, client, temp_data_dir):
        """GET /api/history should return empty list"""
        response = client.get('/api/history')
        
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["success"] is True
        assert isinstance(payload["data"], list)
    
    def test_get_history_with_conversations(self, client, temp_data_dir):
        """GET /api/history should return conversations"""
        from kortex.data import save_conversation, generate_chat_id
        
        chat_id = generate_chat_id()
        save_conversation(chat_id, [], "Test Chat")
        
        response = client.get('/api/history')
        
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["success"] is True
        assert len(payload["data"]) == 1
        assert payload["data"][0]["title"] == "Test Chat"
    
    def test_get_specific_conversation(self, client, temp_data_dir):
        """GET /api/history/<id> should return conversation"""
        from kortex.data import save_conversation, generate_chat_id
        
        chat_id = generate_chat_id()
        messages = [{"role": "user", "content": "Hello"}]
        save_conversation(chat_id, messages, "Test Chat")
        
        response = client.get(f'/api/history/{chat_id}')
        
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["success"] is True
        assert payload["data"]["title"] == "Test Chat"
        assert len(payload["data"]["messages"]) == 1
    
    def test_delete_conversation(self, client, temp_data_dir):
        """DELETE /api/history/<id> should remove conversation"""
        from kortex.data import save_conversation, generate_chat_id, load_conversation
        
        chat_id = generate_chat_id()
        save_conversation(chat_id, [], "To Delete")
        
        response = client.delete(f'/api/history/{chat_id}')
        
        assert response.status_code == 200
        assert load_conversation(chat_id) is None


class TestConfigEndpoints:
    """Tests for /api/config endpoints"""
    
    def test_get_config(self, client, temp_config_file):
        """GET /api/config should return config"""
        response = client.get('/api/config')
        
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["success"] is True
        assert "providers" in payload["data"]
        assert "default_provider" in payload["data"]
        assert "default_model" in payload["data"]
    
    def test_get_api_keys_status(self, client, temp_config_file):
        """GET /api/config/api-keys should return key status"""
        response = client.get('/api/config/api-keys')
        
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["success"] is True
        assert "openai" in payload["data"]
        assert "google" in payload["data"]
        # Should be booleans
        assert isinstance(payload["data"]["openai"], bool)


class TestModelsEndpoints:
    """Tests for /api/models endpoints"""
    
    def test_get_models(self, client, temp_config_file):
        """GET /api/models should return available models"""
        response = client.get('/api/models')
        
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["success"] is True
        assert "providers" in payload["data"]
        assert "current_provider" in payload["data"]
        assert "current_model" in payload["data"]
    
    def test_set_model(self, client, temp_config_file):
        """POST /api/models should change default model"""
        response = client.post(
            '/api/models',
            json={"provider": "google", "model": "gemini-3.1-flash-lite-preview"}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
    
    def test_set_invalid_model(self, client, temp_config_file):
        """POST /api/models with invalid model should fail"""
        response = client.post(
            '/api/models',
            json={"provider": "google", "model": "invalid-model"}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        # Error responses have "error" or "success" = False
        assert "error" in data or data.get("success") is False


class TestBackupEndpoints:
    """Tests for /api/backup/* endpoints"""
    
    def test_get_backup_conversations(self, client, temp_data_dir):
        """GET /api/backup/conversations should return list"""
        from kortex.data import save_conversation, generate_chat_id
        
        chat_id = generate_chat_id()
        save_conversation(chat_id, [], "Backup Test")
        
        response = client.get('/api/backup/conversations')
        
        assert response.status_code == 200
        payload = response.get_json()
        # Response structure: {success: true, data: {conversations: [...]}}
        assert payload["success"] is True
        assert "conversations" in payload["data"]
        assert len(payload["data"]["conversations"]) == 1
    
    def test_download_backup(self, client, temp_data_dir, temp_config_file):
        """POST /api/backup/download should return ZIP"""
        from kortex.data import save_json_file
        
        save_json_file("profile.json", {"name": "Test"})
        
        response = client.post(
            '/api/backup/download',
            json={"conversation_ids": []}
        )
        
        assert response.status_code == 200
        assert response.content_type == 'application/zip'
        assert len(response.data) > 0
