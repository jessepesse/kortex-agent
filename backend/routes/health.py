"""
Health check routes
"""

from backend.errors import success_response


def register_health_routes(app):
    """Register health check endpoints"""
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint for Docker/monitoring"""
        return success_response(data={"status": "healthy", "service": "kortex-backend"})
