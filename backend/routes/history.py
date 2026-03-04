"""
History routes - Conversation management
"""

from kortex import data
from backend.errors import handle_exceptions, NotFoundError, success_response


def register_history_routes(app):
    """Register history/conversation endpoints"""
    
    @app.route('/api/history', methods=['GET'])
    @handle_exceptions
    def get_history():
        """Get list of past conversations"""
        conversations = data.list_conversations()
        return success_response(data=conversations)

    @app.route('/api/history/<chat_id>', methods=['GET'])
    @handle_exceptions
    def get_chat_history(chat_id):
        """Get a specific conversation"""
        conversation = data.load_conversation(chat_id)
        if not conversation:
            raise NotFoundError("Chat not found")
        return success_response(data=conversation)
    
    @app.route('/api/history/<chat_id>', methods=['DELETE'])
    @handle_exceptions
    def delete_history(chat_id):
        """Delete a specific conversation"""
        success = data.delete_conversation(chat_id)
        if not success:
            raise NotFoundError("Conversation not found")
        return success_response(message="Conversation deleted")
    
    @app.route('/api/pin/<chat_id>', methods=['POST'])
    @handle_exceptions
    def pin_conversation(chat_id):
        """Toggle pin status of a conversation"""
        pinned = data.toggle_pin(chat_id)
        if pinned is None:
            raise NotFoundError("Conversation not found")
        return success_response(data={"pinned": pinned})
