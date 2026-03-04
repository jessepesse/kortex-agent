"""
Data routes - JSON data file management
"""

from flask import request

from kortex import data
from backend.errors import handle_exceptions, success_response


def register_data_routes(app):
    """Register data file endpoints"""
    
    @app.route('/api/data', methods=['GET'])
    @handle_exceptions
    def get_all_data():
        """Get all JSON data files"""
        context = data.load_all_context()
        return success_response(data=context)

    @app.route('/api/data/<filename>', methods=['GET'])
    @handle_exceptions
    def get_data_file(filename):
        """Get a specific JSON data file"""
        if not filename.endswith('.json'):
            filename = f"{filename}.json"
        
        file_data = data.load_json_file(filename)
        return success_response(data=file_data)
    
    @app.route('/api/data/<filename>', methods=['PUT'])
    @handle_exceptions
    def update_data_file(filename):
        """Update a specific JSON data file"""
        if not filename.endswith('.json'):
            filename = f"{filename}.json"
        
        body = request.get_json()
        file_data = body.get('data', {})
        
        result = data.save_json_file(filename, file_data)
        return success_response(message=result)
