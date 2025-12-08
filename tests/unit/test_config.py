"""
Unit tests for kortex/config.py
"""

import pytest
import json
import os


class TestLoadConfig:
    """Tests for load_config function"""
    
    def test_load_existing_config(self, temp_config_file):
        """Should load existing config file"""
        from kortex.config import load_config
        
        config = load_config()
        
        assert config["default_provider"] == "google"
        assert config["default_model"] == "gemini-2.5-flash"
        assert "openai" in config["models"]
    
    def test_creates_default_if_not_exists(self, tmp_path, monkeypatch):
        """Should create default config if file doesn't exist"""
        import kortex.config
        
        config_file = tmp_path / "new_config.json"
        monkeypatch.setattr(kortex.config, "CONFIG_FILE", config_file)
        
        config = kortex.config.load_config()
        
        assert config_file.exists()
        assert "api_keys" in config
        assert "models" in config
    
    def test_env_vars_override_config(self, temp_config_file, monkeypatch):
        """Environment variables should override config file values"""
        from kortex.config import load_config
        
        monkeypatch.setenv("OPENAI_API_KEY", "env-openai-key")
        monkeypatch.setenv("GOOGLE_API_KEY", "env-google-key")
        
        config = load_config()
        
        assert config["api_keys"]["openai"] == "env-openai-key"
        assert config["api_keys"]["google"] == "env-google-key"


class TestSaveConfig:
    """Tests for save_config function"""
    
    def test_save_and_reload(self, temp_config_file):
        """Should save config and reload correctly"""
        from kortex.config import load_config, save_config
        
        config = load_config()
        config["default_model"] = "new-model"
        
        save_config(config)
        
        reloaded = load_config()
        assert reloaded["default_model"] == "new-model"
    
    def test_save_preserves_structure(self, temp_config_file):
        """Should preserve JSON structure when saving"""
        from kortex.config import load_config, save_config
        
        config = load_config()
        original_keys = set(config.keys())
        
        config["new_field"] = "new_value"
        save_config(config)
        
        reloaded = load_config()
        assert set(reloaded.keys()) == original_keys | {"new_field"}
