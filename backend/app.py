#!/usr/bin/env python3
"""
Flask Backend Server for Kortex Agent
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask
from flask_cors import CORS
from routes import register_all_routes
from errors import register_error_handlers

app = Flask(__name__)

# Configure CORS properly - allow all origins in development
CORS(app)

# Register all routes from modular structure
register_all_routes(app)

# Register global error handlers for consistent error responses
register_error_handlers(app)

@app.route('/health')
def health():
    return {"status": "ok", "service": "Kortex Agent Backend"}


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
    
    app.run(host='0.0.0.0', port=5001, debug=True)
