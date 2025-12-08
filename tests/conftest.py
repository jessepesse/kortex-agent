"""
Pytest configuration and shared fixtures for Kortex Agent tests
"""

import pytest
import tempfile
import shutil
import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_data_dir(tmp_path, monkeypatch):
    """Create a temporary data directory for tests."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Patch DATA_DIR in kortex.config
    import kortex.config
    monkeypatch.setattr(kortex.config, "DATA_DIR", data_dir)
    
    # Also patch in kortex.data
    import kortex.data
    monkeypatch.setattr("kortex.data.DATA_DIR", data_dir)
    
    # Also patch in kortex.tools
    import kortex.tools
    monkeypatch.setattr("kortex.tools.DATA_DIR", data_dir)
    
    # Also patch in kortex.backup
    import kortex.backup
    monkeypatch.setattr("kortex.backup.DATA_DIR", data_dir)
    
    return data_dir


@pytest.fixture
def temp_config_file(tmp_path, monkeypatch):
    """Create a temporary config file for tests."""
    config_file = tmp_path / "config.json"
    
    default_config = {
        "api_keys": {"openai": "", "google": "", "anthropic": ""},
        "default_provider": "google",
        "default_model": "gemini-2.5-flash",
        "models": {
            "openai": ["gpt-5", "gpt-5-mini"],
            "google": ["gemini-2.5-flash", "gemini-2.5-flash-lite"],
            "anthropic": ["claude-haiku-4-5"]
        }
    }
    
    with open(config_file, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    import kortex.config
    monkeypatch.setattr(kortex.config, "CONFIG_FILE", config_file)
    
    return config_file


@pytest.fixture
def sample_profile_data():
    """Sample profile data for testing."""
    return {
        "name": "Test User",
        "location": "Helsinki",
        "timezone": "Europe/Helsinki",
        "language": "Finnish",
        "occupation": "Developer",
        "bio": "Test bio"
    }


@pytest.fixture
def sample_health_data():
    """Sample health data for testing."""
    return {
        "current_state": {
            "physical": "good",
            "mental": "focused",
            "energy": 8,
            "sleep_quality": "good",
            "last_updated": "2024-01-01"
        },
        "conditions": [],
        "medications": [],
        "exercise_log": [],
        "notes": []
    }


@pytest.fixture
def flask_test_client(temp_data_dir, temp_config_file):
    """Create Flask test client."""
    from backend.app import create_app
    
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_api_keys(monkeypatch):
    """Mock API keys for testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
