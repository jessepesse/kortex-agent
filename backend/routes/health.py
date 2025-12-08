"""
Health check routes
"""

from flask import jsonify


def register_health_routes(app):
    """Register health check endpoints"""
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint for Docker/monitoring"""
        return jsonify({"status": "healthy", "service": "kortex-backend"})
