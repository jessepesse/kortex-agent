"""
Kortex Agent - Personal AI Assistant Package

A pragmatic AI-powered life management system with Council LLM architecture.
Supporting multiple LLM providers (Google Gemini, OpenAI, Anthropic).
"""

__version__ = "1.0.0-rc2"

from . import config
from . import data
from . import tools
from . import backup

__all__ = ["config", "data", "tools", "backup"]
