"""
Centralized error handling for Kortex Agent Backend

Provides consistent error responses and global exception handlers.
"""

from __future__ import annotations

import traceback
from functools import wraps
from typing import Any, Callable, TypeVar

from flask import jsonify, Response


# Type for decorated functions
F = TypeVar('F', bound=Callable[..., Any])


class APIError(Exception):
    """Base exception for API errors with status code."""
    
    def __init__(self, message: str, status_code: int = 400, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(APIError):
    """Resource not found error (404)."""
    
    def __init__(self, message: str = "Resource not found", details: dict[str, Any] | None = None):
        super().__init__(message, 404, details)


class ValidationError(APIError):
    """Validation error (400)."""
    
    def __init__(self, message: str = "Validation failed", details: dict[str, Any] | None = None):
        super().__init__(message, 400, details)


class ConfigurationError(APIError):
    """Configuration error (400)."""
    
    def __init__(self, message: str = "Configuration error", details: dict[str, Any] | None = None):
        super().__init__(message, 400, details)


def error_response(
    message: str, 
    status_code: int = 400, 
    details: dict[str, Any] | None = None
) -> tuple[Response, int]:
    """
    Create a standardized error response.
    
    Format:
    {
        "error": true,
        "message": "Error description",
        "details": {...}  # Optional additional info
    }
    """
    response = {
        "error": True,
        "message": message
    }
    
    if details:
        response["details"] = details
    
    return jsonify(response), status_code


def success_response(
    data: Any = None, 
    message: str | None = None
) -> Response:
    """
    Create a standardized success response.
    
    Format:
    {
        "success": true,
        "message": "Optional message",
        "data": {...}
    }
    """
    response: dict[str, Any] = {"success": True}
    
    if message:
        response["message"] = message
    
    if data is not None:
        response["data"] = data
    
    return jsonify(response)


def handle_exceptions(f: F) -> F:
    """
    Decorator for route handlers that provides consistent exception handling.
    
    Usage:
        @app.route('/api/example')
        @handle_exceptions
        def example_route():
            ...
    """
    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return f(*args, **kwargs)
        except APIError as e:
            return error_response(e.message, e.status_code, e.details)
        except Exception as e:
            # Log the full traceback for debugging
            traceback.print_exc()
            
            # Check debug mode
            import os
            debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
            
            if debug_mode:
                return error_response(f"Internal server error: {str(e)}", 500)
            else:
                return error_response("An internal server error occurred.", 500)
    
    return wrapper  # type: ignore


def handle_async_exceptions(f: F) -> F:
    """
    Decorator for async route handlers with consistent exception handling.
    
    Usage:
        @app.route('/api/example')
        @handle_async_exceptions
        async def example_route():
            ...
    """
    @wraps(f)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await f(*args, **kwargs)
        except APIError as e:
            return error_response(e.message, e.status_code, e.details)
        except Exception as e:
            traceback.print_exc()
            
            # Check debug mode
            import os
            debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
            
            if debug_mode:
                return error_response(f"Internal server error: {str(e)}", 500)
            else:
                return error_response("An internal server error occurred.", 500)
    
    return wrapper  # type: ignore


def register_error_handlers(app: Any) -> None:
    """
    Register global error handlers with Flask app.
    
    Call this during app initialization:
        register_error_handlers(app)
    """
    
    @app.errorhandler(APIError)
    def handle_api_error(error: APIError) -> tuple[Response, int]:
        return error_response(error.message, error.status_code, error.details)
    
    @app.errorhandler(404)
    def handle_not_found(error: Any) -> tuple[Response, int]:
        return error_response("Endpoint not found", 404)
    
    @app.errorhandler(405)
    def handle_method_not_allowed(error: Any) -> tuple[Response, int]:
        return error_response("Method not allowed", 405)
    
    @app.errorhandler(500)
    def handle_internal_error(error: Any) -> tuple[Response, int]:
        traceback.print_exc()
        return error_response("Internal server error", 500)
