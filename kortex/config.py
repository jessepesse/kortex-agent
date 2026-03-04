"""Configuration management for Kortex Agent"""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging import (avoid circular import)
import logging
logger = logging.getLogger(__name__)

# Paths
BASE_DIR: Path = Path(__file__).parent.parent
DATA_DIR: Path = BASE_DIR / "data"
CONFIG_FILE: Path = BASE_DIR / "config.json"


def load_config() -> ConfigDict:
    """Load configuration from config.json and environment variables."""
    config: ConfigDict = {}
    
    if not CONFIG_FILE.exists():
        default_config: ConfigDict = {
            "api_keys": {"openai": "", "google": "", "anthropic": "", "openrouter": ""},
            "default_provider": "google",
            "default_model": "gemini-3-flash-preview",
            "models": {
                "openai": [
                    {"id": "gpt-5"},
                    {"id": "gpt-5-mini"},
                    {"id": "gpt-5-nano"},
                    {"id": "gpt-5.1"}
                ],
                "google": [
                    {"id": "gemini-3-pro-preview"},
                    {"id": "gemini-3.1-pro-preview"},
                    {"id": "gemini-3-flash-preview"},
                    {"id": "gemini-3.1-flash-lite-preview"}
                ],
                "anthropic": [
                    {"id": "claude-opus-4-6"},
                    {"id": "claude-opus-4-5"},
                    {"id": "claude-sonnet-4-6"},
                    {"id": "claude-haiku-4-5"}
                ],
                "openrouter": [
                    {"id": "gemini-3-flash-preview", "thinking": True}
                ]
            }
        }
        save_config(default_config)
        config = default_config
    else:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            
    # Override with environment variables if present
    if os.getenv("OPENAI_API_KEY"):
        config["api_keys"]["openai"] = os.getenv("OPENAI_API_KEY", "")
        
    if os.getenv("GOOGLE_API_KEY"):
        config["api_keys"]["google"] = os.getenv("GOOGLE_API_KEY", "")

    if os.getenv("ANTHROPIC_API_KEY"):
        config["api_keys"]["anthropic"] = os.getenv("ANTHROPIC_API_KEY", "")
    
    if os.getenv("OPENROUTER_API_KEY"):
        config["api_keys"]["openrouter"] = os.getenv("OPENROUTER_API_KEY", "")
        
    return config


def save_config(config: ConfigDict) -> None:
    """Save configuration to config.json."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def setup_api_keys(config: ConfigDict) -> ConfigDict:
    """Interactive setup for API keys if missing."""
    needs_save = False
    
    # Check OpenAI key
    if not config["api_keys"]["openai"]:
        openai_key = os.environ.get("OPENAI_API_KEY", "")
        if not openai_key:
            logger.info("OpenAI API Key not found.")
            openai_key = input("Enter your OpenAI API key (or press Enter to skip): ").strip()
        
        if openai_key:
            config["api_keys"]["openai"] = openai_key
            needs_save = True
    
    # Check Google key
    if not config["api_keys"]["google"]:
        google_key = os.environ.get("GOOGLE_API_KEY", "")
        if not google_key:
            logger.info("Google Gemini API Key not found.")
            google_key = input("Enter your Gemini API key (or press Enter to skip): ").strip()
        
        if google_key:
            config["api_keys"]["google"] = google_key
            needs_save = True

    # Check Anthropic key
    if not config["api_keys"].get("anthropic"):
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not anthropic_key:
            logger.info("Anthropic API Key not found.")
            anthropic_key = input("Enter your Anthropic API key (or press Enter to skip): ").strip()
        
        if anthropic_key:
            if "anthropic" not in config["api_keys"]:
                config["api_keys"]["anthropic"] = ""
            config["api_keys"]["anthropic"] = anthropic_key
            needs_save = True
    
    if needs_save:
        save_config(config)
        logger.info("API keys saved to config.json")
    
    return config
