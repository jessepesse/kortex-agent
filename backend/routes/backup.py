"""
Backup routes - Backup and restore functionality
"""

from flask import request, Response

from kortex import data, backup
from errors import handle_exceptions, ValidationError, success_response


def register_backup_routes(app):
    """Register backup/restore endpoints"""

    @app.route('/api/backup/conversations', methods=['GET'])
    @handle_exceptions
    def get_backup_conversations():
        """Get list of conversations for backup selection"""
        conversations = data.list_conversations()
        return success_response(data={"conversations": conversations})

    @app.route('/api/backup/download', methods=['POST'])
    @handle_exceptions
    def download_backup():
        """Create and download a backup ZIP file"""
        req_data = request.get_json() or {}
        conversation_ids = req_data.get('conversation_ids')
        
        zip_bytes = backup.create_backup(conversation_ids)
        filename = backup.get_backup_filename()
        
        return Response(
            zip_bytes,
            mimetype='application/zip',
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Length': len(zip_bytes)
            }
        )

    @app.route('/api/backup/validate', methods=['POST'])
    @handle_exceptions
    def validate_backup_file():
        """Validate an uploaded backup file"""
        if 'file' not in request.files:
            raise ValidationError("No file uploaded")
        
        file = request.files['file']
        if file.filename == '':
            raise ValidationError("No file selected")
        
        zip_bytes = file.read()
        result = backup.validate_backup(zip_bytes)
        
        return success_response(data=result)

    @app.route('/api/backup/restore', methods=['POST'])
    @handle_exceptions
    def restore_backup_file():
        """Restore from an uploaded backup file"""
        if 'file' not in request.files:
            raise ValidationError("No file uploaded")
        
        file = request.files['file']
        if file.filename == '':
            raise ValidationError("No file selected")
        
        zip_bytes = file.read()
        result = backup.restore_backup(zip_bytes)
        
        return success_response(data=result)
