#!/usr/bin/env python3
"""
Flask Backend Server for Kortex Agent
"""

import os
import sys
import hmac
from pathlib import Path

# Add parent directory to path for kortex imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, request
from flask_cors import CORS
from backend.routes import register_all_routes
from backend.errors import register_error_handlers
from backend.errors import error_response


def resolve_bind_host() -> str:
    """Resolve backend bind host.

    Security default is localhost-only. Set KORTEX_BIND_HOST explicitly
    (e.g. 0.0.0.0) only for trusted local container networking.
    """
    return os.getenv('KORTEX_BIND_HOST', '127.0.0.1')


def is_api_auth_enabled() -> bool:
    """Return whether API token auth is enabled."""
    return os.getenv('KORTEX_REQUIRE_AUTH', 'false').lower() == 'true'


def get_api_auth_token() -> str:
    """Return configured API auth token (empty if unset)."""
    return os.getenv('KORTEX_API_TOKEN', '')


def _should_require_auth(path: str) -> bool:
    """Require auth for all API routes except health checks."""
    if path == '/api/health':
        return False
    return path.startswith('/api/')


def _extract_bearer_token(auth_header: str | None) -> str:
    if not auth_header:
        return ''
    if not auth_header.startswith('Bearer '):
        return ''
    return auth_header[7:].strip()


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

    @application.before_request
    def require_api_auth():
        if not is_api_auth_enabled():
            return None

        if not _should_require_auth(request.path):
            return None

        expected_token = get_api_auth_token()
        if not expected_token:
            return error_response(
                "API auth is enabled but KORTEX_API_TOKEN is not set.",
                503,
            )

        provided_token = _extract_bearer_token(request.headers.get('Authorization'))
        if not provided_token or not hmac.compare_digest(provided_token, expected_token):
            return error_response("Unauthorized", 401)

        return None
    
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

    bind_host = resolve_bind_host()
    if bind_host != '127.0.0.1':
        print(f"⚠️  WARNING: Backend binding to {bind_host}.")
        print("⚠️  Kortex is intended for local use only. Do not expose to public network.")
        if not is_api_auth_enabled():
            print("⚠️  Consider setting KORTEX_REQUIRE_AUTH=true and KORTEX_API_TOKEN for non-local deployments.")

    app.run(host=bind_host, port=5001, debug=debug_mode) # nosec B104
