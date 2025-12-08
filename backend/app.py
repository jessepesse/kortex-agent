#!/usr/bin/env python3
"""
Flask Backend Server for Kortex Agent
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for kortex imports
sys.path.insert(0, str(Path(__file__).parent.parent))
# Add backend directory to path for routes/errors imports
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask
from flask_cors import CORS
from routes import register_all_routes
from errors import register_error_handlers


def create_app():
    """Application factory for Flask app.
    
    Returns:
        Flask app instance configured with all routes and error handlers.
    """
    application = Flask(__name__)
    
    # Configure CORS properly - allow frontend origin
    allowed_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
    CORS(application, resources={r"/api/*": {"origins": allowed_origins}}, supports_credentials=True)
    
    # Register all routes from modular structure
    register_all_routes(application)
    
    # Register global error handlers for consistent error responses
    register_error_handlers(application)
    
    @application.route('/health')
    def health():
        return {"status": "ok", "service": "Kortex Agent Backend"}
    
    return application


# Global app instance for direct execution
app = create_app()


# Start background services
def start_background_services():
    """Initialize background services"""
    from kortex.background import get_title_fixer
    
    # Start title fixer (runs every 24 hours)
    title_fixer = get_title_fixer(interval_hours=24)
    title_fixer.start()


if __name__ == '__main__':
    print("=" * 60)
    print("🧠 Kortex Agent Backend - Starting...")
    print("=" * 60)
    print("API will be available at: http://localhost:5001")
    print("Health check: http://localhost:5001/health")
    print("=" * 60)
    
    # Start background services
    start_background_services()
    
    # Security: Debug mode disabled by default, controlled via env var
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    if debug_mode:
        print("⚠️  WARNING: Debug mode is ENABLED")
    
    app.run(host='0.0.0.0', port=5001, debug=debug_mode)
