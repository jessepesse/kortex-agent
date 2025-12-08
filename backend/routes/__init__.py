"""
Routes package for Kortex Agent Backend
Split into modular route files for maintainability
"""

import sys
from pathlib import Path

# Add parent directory to path for kortex imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .health import register_health_routes
from .chat import register_chat_routes
from .history import register_history_routes
from .data import register_data_routes
from .config import register_config_routes
from .backup import register_backup_routes
from .council import register_council_routes


def register_all_routes(app):
    """Register all API routes from submodules"""
    register_health_routes(app)
    register_chat_routes(app)
    register_history_routes(app)
    register_data_routes(app)
    register_config_routes(app)
    register_backup_routes(app)
    register_council_routes(app)
