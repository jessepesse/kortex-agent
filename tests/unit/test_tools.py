"""
Unit tests for kortex/tools.py
"""

import pytest


class TestToolFunctions:
    """Tests for tool execution functions"""
    
    def test_update_profile(self, temp_data_dir):
        """Should update profile data"""
        from kortex.tools import update_profile
        from kortex.data import load_json_file
        
        result = update_profile({"name": "New Name", "location": "Helsinki"})
        
        assert "updated" in result.lower() or "profile" in result.lower()
        
        profile = load_json_file("profile.json")
        assert profile["name"] == "New Name"
        assert profile["location"] == "Helsinki"
    
    def test_update_health(self, temp_data_dir):
        """Should update health data"""
        from kortex.tools import update_health
        from kortex.data import load_json_file
        
        result = update_health({"current_state": {"energy": 8}})
        
        assert "updated" in result.lower() or "health" in result.lower()
        
        health = load_json_file("health.json")
        assert health["current_state"]["energy"] == 8
    
    def test_update_profile_invalid_data(self, temp_data_dir):
        """Should handle invalid data gracefully"""
        from kortex.tools import update_profile
        
        result = update_profile("not a dict")
        
        assert "error" in result.lower()
    
    def test_create_data_file(self, temp_data_dir):
        """Should create new data file"""
        from kortex.tools import create_data_file
        from kortex.data import load_json_file
        
        result = create_data_file("books.json", {"books": []})
        
        assert "created" in result.lower() or "✓" in result
        
        books = load_json_file("books.json")
        assert "books" in books
    
    def test_create_data_file_already_exists(self, temp_data_dir):
        """Should fail if file already exists"""
        from kortex.tools import create_data_file
        from kortex.data import save_json_file
        
        save_json_file("existing.json", {})
        
        result = create_data_file("existing.json", {})
        
        assert "error" in result.lower() or "exists" in result.lower()
    
    def test_update_data_file(self, temp_data_dir):
        """Should update any data file"""
        from kortex.tools import update_data_file
        from kortex.data import save_json_file, load_json_file
        
        save_json_file("custom.json", {"key1": "value1"})
        
        result = update_data_file("custom.json", {"key2": "value2"})
        
        assert "updated" in result.lower()
        
        data = load_json_file("custom.json")
        assert data["key1"] == "value1"  # Preserved
        assert data["key2"] == "value2"  # Added
    
    def test_list_data_files(self, temp_data_dir):
        """Should list all data files"""
        from kortex.tools import list_data_files
        from kortex.data import save_json_file
        
        save_json_file("file1.json", {})
        save_json_file("file2.json", {})
        
        result = list_data_files()
        
        assert "file1.json" in result
        assert "file2.json" in result


class TestToolDefinitions:
    """Tests for tool definitions structure"""
    
    def test_tool_functions_mapping_complete(self):
        """TOOL_FUNCTIONS should have all expected functions"""
        from kortex.tools import TOOL_FUNCTIONS
        
        expected = [
            "update_profile",
            "update_health",
            "update_values",
            "update_finance",
            "update_routines",
            "create_data_file",
            "update_data_file",
            "list_data_files"
        ]
        
        for name in expected:
            assert name in TOOL_FUNCTIONS
            assert callable(TOOL_FUNCTIONS[name])
    
    def test_tool_definitions_structure(self):
        """TOOL_DEFINITIONS should have correct OpenAI format"""
        from kortex.tools import TOOL_DEFINITIONS
        
        for tool in TOOL_DEFINITIONS:
            assert "type" in tool
            assert tool["type"] == "function"
            assert "function" in tool
            assert "name" in tool["function"]
            assert "description" in tool["function"]
            assert "parameters" in tool["function"]
    
    def test_gemini_tool_definitions_structure(self):
        """GEMINI_TOOL_DEFINITIONS should have correct Gemini format"""
        from kortex.tools import GEMINI_TOOL_DEFINITIONS
        
        for tool in GEMINI_TOOL_DEFINITIONS:
            assert "name" in tool
            assert "description" in tool
            assert "parameters" in tool
            
            # Should use uppercase types for Gemini
            params = tool["parameters"]
            assert params["type"] == "OBJECT"
    
    def test_definitions_match_functions(self):
        """All defined tools should have implementations"""
        from kortex.tools import TOOL_FUNCTIONS, GEMINI_TOOL_DEFINITIONS
        
        for tool in GEMINI_TOOL_DEFINITIONS:
            name = tool["name"]
            assert name in TOOL_FUNCTIONS, f"No implementation for {name}"
