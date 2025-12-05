"""
Flask API Routes for Kortex Agent Backend
Handles all API endpoints for the web UI
"""

from flask import request, jsonify, session
from pathlib import Path
import json
import sys
import os
import asyncio
from dotenv import load_dotenv

# Add parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent / ".env")

# Import from kortex package
from kortex import config, data, backup
from kortex.ai import handler as ai_handler

# Configuration
CONFIG_FILE = config.CONFIG_FILE


def load_config():
    """Load configuration using kortex.config module"""
    return config.load_config()


def save_config(cfg):
    """Save configuration using kortex.config module"""
    config.save_config(cfg)


def register_routes(app):
    """Register all API routes"""
    
    @app.route('/api/chat', methods=['POST'])
    async def chat():
        """
        Send a chat message to AI
        
        Request body:
        {
            "message": str,
            "history": list[dict],  # Optional chat history
            "model": str,           # Optional, uses default if not provided
            "provider": str         # Optional, uses default if not provided
        }
        
        Response:
        {
            "response": str or None,
            "function_calls": list or None,
            "error": str or None
        }
        """
        try:
            request_data = request.get_json()
            message = request_data.get('message', '')
            history = request_data.get('history', [])
            files = request_data.get('files', [])  # Extract uploaded files
            
            if not message and not files:
                return jsonify({"error": "Message or files required"}), 400
            
            # Get config
            config = load_config()
            
            # Use provided model/provider or defaults
            provider = request_data.get('provider', config['default_provider'])
            model = request_data.get('model', config['default_model'])
            
            # Get API key for provider
            api_key = config['api_keys'].get(provider)
            if not api_key:
                return jsonify({"error": f"No API key configured for {provider}"}), 400
            
            # Generate or use existing chat_id
            chat_id = request_data.get('chat_id')
            if not chat_id:
                chat_id = data.generate_chat_id()
                
            # Initialize Scribe
            from kortex.ai.scribe import ScribeService
            scribe = ScribeService()
            
            # Load context for Scribe
            from kortex import data as kortex_data
            context = kortex_data.load_all_context()
            
            # Run Chat and Scribe SEQUENTIALLY
            # 1. Main Chat Task (Synchronous, run in executor)
            loop = asyncio.get_event_loop()
            chat_result = await loop.run_in_executor(
                None, 
                ai_handler.get_ai_response, 
                message, history, model, provider, api_key, files
            )
            
            # Ensure we have valid response content for Scribe
            response_content = chat_result.get("response") or chat_result.get("error") or "(No response)"
            
            # 2. Scribe Task (Async background data update) - Now with FULL context
            scribe_updates = await scribe.analyze_and_update(message, response_content, context, history)
            
            # Update history with new messages
            new_history = history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": response_content}
            ]
            
            
            
            # Save conversation with AI-generated title
            # First, check if this conversation already has a title
            existing_title = None
            if chat_id:
                try:
                    existing_conv = data.load_conversation(chat_id)
                    if existing_conv:
                        existing_title = existing_conv.get('title')
                except Exception:
                    pass
            
            # Use existing title if available, otherwise generate new one
            title = existing_title or request_data.get('title', 'New Chat')
            
            # Generate title using AI for new chats (first 2 messages)
            if len(new_history) <= 2:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=config['api_keys'].get('google'))
                    
                    title_model = genai.GenerativeModel('gemini-2.5-flash-lite')
                    title_prompt = f"""Generate a short, concise title (max 40 characters) for this conversation.
User message: {message}
AI response: {response_content[:200]}

Respond with ONLY the title, no quotes or extra text. Be specific and descriptive."""
                    
                    title_response = title_model.generate_content(title_prompt)
                    
                    if hasattr(title_response, 'text') and title_response.text:
                        title = title_response.text.strip()[:50]
                        print(f"📝 Generated title: '{title}'")
                    else:
                        title = message[:40] + "..." if len(message) > 40 else message
                        
                except Exception as e:
                    print(f"⚠️ Failed to generate title: {e}")
                    title = message[:40] + "..." if len(message) > 40 else message
                
            data.save_conversation(chat_id, new_history, title)
            
            # Ensure a textual response is always present
            if not chat_result.get('response') and chat_result.get('function_calls'):
                chat_result['response'] = "I've executed the requested action(s) and updated your data accordingly."

            # Combine results
            response_data = chat_result
            response_data['chat_id'] = chat_id
            
            # If Scribe made updates, append them to the response
            if scribe_updates:
                scribe_msg = "\n".join(scribe_updates)
                # We can append this to the response text or send it as a separate field
                # For now, let's append it as a system note
                response_data['scribe_updates'] = scribe_updates
            
            return jsonify(response_data)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500
            
            
    @app.route('/api/history', methods=['GET'])
    def get_history():
        """Get list of past conversations"""
        try:
            conversations = data.list_conversations()
            return jsonify(conversations)
        except Exception as e:
            return jsonify({"error": str(e)}), 500


    @app.route('/api/history/<chat_id>', methods=['GET'])
    def get_chat_history(chat_id):
        """Get a specific conversation"""
        try:
            conversation = data.load_conversation(chat_id)
            if not conversation:
                return jsonify({"error": "Chat not found"}), 404
            return jsonify(conversation)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/history/<chat_id>', methods=['DELETE'])
    def delete_history(chat_id):
        """Delete a specific conversation"""
        try:
            success = data.delete_conversation(chat_id)
            if success:
                return jsonify({"success": True})
            else:
                return jsonify({"error": "Conversation not found"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500


    @app.route('/api/data', methods=['GET'])
    def get_all_data():
        """
        Get all JSON data files
        
        Response:
        {
            "profile": {...},
            "health": {...},
            ..}
        }
        """
        try:
            context = data.load_all_context()
            return jsonify(context)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    
    @app.route('/api/council', methods=['POST'])
    async def council():
        """
        Trigger Council Mode: Query multiple models and synthesize
        """
        try:
            request_data = request.get_json()
            message = request_data.get('message', '')
            history = request_data.get('history', [])
            
            if not message:
                return jsonify({"error": "Message is required"}), 400
            
            # Load context
            context = data.load_all_context()
            
            # Initialize service
            from kortex.ai.council import CouncilService
            service = CouncilService()
            
            # Get response
            result = await service.get_council_response(message, history, context)
            
            # Save conversation with AI-generated title
            chat_id = request_data.get('chat_id')
            if not chat_id:
                import time, random
                chat_id = f"{int(time.time())}_{hex(random.randint(0, 0xFFFFFFFF))[2:]}"
            
            # Check for existing title
            existing_title = None
            if chat_id:
                try:
                    existing_conv = data.load_conversation(chat_id)
                    if existing_conv:
                        existing_title = existing_conv.get('title')
                except Exception:
                    pass
            
            title = existing_title or 'New Chat'
            
            # Generate title for new chats (only from user message, not council response)
            if len(history) <= 2:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=config['api_keys'].get('google'))
                    
                    title_model = genai.GenerativeModel('gemini-2.5-flash-lite')
                    title_prompt = f"""Generate a short, concise title (max 40 characters) for this Elite Council discussion.
User question: {message}

Respond with ONLY the title in Finnish, no quotes or extra text. Be specific and descriptive."""
                    
                    title_response = title_model.generate_content(title_prompt)
                    
                    if hasattr(title_response, 'text') and title_response.text:
                        title = title_response.text.strip()[:50]
                        print(f"📝 Generated Elite title: '{title}'")
                    else:
                        title = message[:40] + "..." if len(message) > 40 else message
                        
                except Exception as e:
                    print(f"⚠️ Failed to generate title: {e}")
                    title = message[:40] + "..." if len(message) > 40 else message
            
            # Update history
            new_history = history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": result.get('chairman_response', ''), "council_type": "elite"}
            ]
            
            data.save_conversation(chat_id, new_history, title)
            
            return jsonify(result)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/hive', methods=['POST'])
    async def hive():
        """
        Trigger Hive Mode: 6 DeepSeek personas with specialized roles
        """
        try:
            request_data = request.get_json()
            message = request_data.get('message', '')
            history = request_data.get('history', [])
            
            if not message:
                return jsonify({"error": "Message is required"}), 400
            
            # Load context
            context = data.load_all_context()
            
            # Initialize Hive service
            from kortex.ai.hive import HiveService
            service = HiveService()
            
            # Get response
            result = await service.get_hive_response(message, history, context)
            
            # Save conversation with AI-generated title
            chat_id = request_data.get('chat_id')
            if not chat_id:
                import time, random
                chat_id = f"{int(time.time())}_{hex(random.randint(0, 0xFFFFFFFF))[2:]}"
            
            # Check for existing title
            existing_title = None
            if chat_id:
                try:
                    existing_conv = data.load_conversation(chat_id)
                    if existing_conv:
                        existing_title = existing_conv.get('title')
                except Exception:
                    pass
            
            title = existing_title or 'New Chat'
            
            # Generate title for new chats (only from user message, not hive response)
            if len(history) <= 2:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=config['api_keys'].get('google'))
                    
                    title_model = genai.GenerativeModel('gemini-2.5-flash-lite')
                    title_prompt = f"""Generate a short, concise title (max 40 characters) for this Hive Council discussion.
User question: {message}

Respond with ONLY the title in Finnish, no quotes or extra text. Be specific and descriptive."""
                    
                    title_response = title_model.generate_content(title_prompt)
                    
                    if hasattr(title_response, 'text') and title_response.text:
                        title = title_response.text.strip()[:50]
                        print(f"🐝 Generated Hive title: '{title}'")
                    else:
                        title = message[:40] + "..." if len(message) > 40 else message
                        
                except Exception as e:
                    print(f"⚠️ Failed to generate title: {e}")
                    title = message[:40] + "..." if len(message) > 40 else message
            
            # Update history
            new_history = history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": result.get('chairman_response', ''), "council_type": "hive"}
            ]
            
            data.save_conversation(chat_id, new_history, title)
            
            return jsonify(result)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/mega', methods=['POST'])
    async def mega():
        """
        Trigger MEGA Mode: Elite + Hive battle → Ultimate Chairman
        """
        try:
            request_data = request.get_json()
            message = request_data.get('message', '')
            history = request_data.get('history', [])
            
            if not message:
                return jsonify({"error": "Message is required"}), 400
            
            # Load context
            context = data.load_all_context()
            
            # Initialize Mega service
            from kortex.ai.mega import MegaCouncilService
            service = MegaCouncilService()
            
            # Get response
            result = await service.get_mega_response(message, history, context)
            
            # Save conversation with AI-generated title
            chat_id = request_data.get('chat_id')
            if not chat_id:
                import time, random
                chat_id = f"{int(time.time())}_{hex(random.randint(0, 0xFFFFFFFF))[2:]}"
            
            # Check for existing title
            existing_title = None
            if chat_id:
                try:
                    existing_conv = data.load_conversation(chat_id)
                    if existing_conv:
                        existing_title = existing_conv.get('title')
                except Exception:
                    pass
            
            title = existing_title or 'New Chat'
            
            # Generate title for new chats (only from user message)
            if len(history) <= 2:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=config['api_keys'].get('google'))
                    
                    title_model = genai.GenerativeModel('gemini-2.5-flash-lite')
                    title_prompt = f"""Generate a short, concise title (max 40 characters) for this MEGA Council discussion.
User question: {message}

Respond with ONLY the title in Finnish, no quotes or extra text. Be specific and descriptive."""
                    
                    title_response = title_model.generate_content(title_prompt)
                    
                    if hasattr(title_response, 'text') and title_response.text:
                        title = title_response.text.strip()[:50]
                        print(f"🔥 Generated Mega title: '{title}'")
                    else:
                        title = message[:40] + "..." if len(message) > 40 else message
                        
                except Exception as e:
                    print(f"⚠️ Failed to generate title: {e}")
                    title = message[:40] + "..." if len(message) > 40 else message
            
            # Update history
            new_history = history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": result.get('mega_verdict', ''), "council_type": "mega"}
            ]
            
            data.save_conversation(chat_id, new_history, title)
            
            return jsonify(result)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500


    @app.route('/api/data/<filename>', methods=['GET'])
    def get_data_file(filename):
        """
        Get a specific JSON data file
        
        Response:
        {
            "data": {...}
        }
        """
        try:
            # Ensure filename ends with .json
            if not filename.endswith('.json'):
                filename = f"{filename}.json"
            
            file_data = data.load_json_file(filename)
            return jsonify({"data": file_data})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    
    @app.route('/api/data/<filename>', methods=['PUT'])
    def update_data_file(filename):
        """
        Update a specific JSON data file
        
        Request body:
        {
            "data": {...}
        }
        
        Response:
        {
            "success": bool,
            "message": str
        }
        """
        try:
            # Ensure filename ends with .json
            if not filename.endswith('.json'):
                filename = f"{filename}.json"
            
            body = request.get_json()
            file_data = body.get('data', {})
            
            result = data.save_json_file(filename, file_data)
            return jsonify({"success": True, "message": result})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
    
    
    @app.route('/api/models', methods=['GET'])
    def get_models():
        """
        Get available models and current selection
        
        Response:
        {
            "providers": {
                "openai": ["gpt-5", ...],
                "google": ["gemini-2.5-flash", ...]
            },
            "current_provider": str,
            "current_model": str
        }
        """
        try:
            config = load_config()
            return jsonify({
                "providers": config['models'],
                "current_provider": config['default_provider'],
                "current_model": config['default_model']
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/pin/<chat_id>', methods=['POST'])
    def pin_conversation(chat_id):
        """Toggle pin status of a conversation"""
        try:
            pinned = data.toggle_pin(chat_id)
            if pinned is None:
                return jsonify({"error": "Conversation not found"}), 404
            return jsonify({"pinned": pinned})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    
    @app.route('/api/models', methods=['POST'])
    def set_model():
        """
        Set the default model and provider
        
        Request body:
        {
            "provider": str,
            "model": str
        }
        
        Response:
        {
            "success": bool,
            "message": str
        }
        """
        try:
            data = request.get_json()
            provider = data.get('provider')
            model = data.get('model')
            
            if not provider or not model:
                return jsonify({"success": False, "message": "Provider and model are required"}), 400
            
            config = load_config()
            
            # Validate provider and model
            if provider not in config['models']:
                return jsonify({"success": False, "message": f"Invalid provider: {provider}"}), 400
            
            if model not in config['models'][provider]:
                return jsonify({"success": False, "message": f"Invalid model: {model}"}), 400
            
            # Update config
            config['default_provider'] = provider
            config['default_model'] = model
            save_config(config)
            
            return jsonify({"success": True, "message": f"Switched to {provider}: {model}"})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
    
    
    @app.route('/api/function-call/execute', methods=['POST'])
    def execute_function_call():
        """
        Execute a function call (after user approval)
        
        Request body:
        {
            "function_name": str,
            "args": {...}
        }
        
        Response:
        {
            "success": bool,
            "message": str
        }
        """
        try:
            request_data = request.get_json()
            function_name = request_data.get('function_name')
            args = request_data.get('args', {})
            
            if not function_name:
                return jsonify({"success": False, "message": "Function name is required"}), 400
            
            result = ai_handler.execute_function(function_name, args)
            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    # Configuration endpoints
    @app.route('/api/config', methods=['GET'])
    def get_config():
        """Get current configuration including available models"""
        try:
            cfg = config.load_config()
            return jsonify({
                'providers': cfg.get('models', {}),
                'default_provider': cfg.get('default_provider', 'google'),
                'default_model': cfg.get('default_model', 'gemini-2.5-flash')
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/config/api-keys', methods=['GET'])
    def get_api_keys_status():
        """
        Check which API keys are configured (without revealing the keys)
        
        Response:
        {
            "openai": bool,
            "google": bool
        }
        """
        try:
            config = load_config()
            return jsonify({
                "openai": bool(config['api_keys'].get('openai')),
                "google": bool(config['api_keys'].get('google'))
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    
    @app.route('/api/config/api-keys', methods=['POST'])
    def set_api_keys():
        """
        Set API keys
        
        Request body:
        {
            "openai": str (optional),
            "google": str (optional)
        }
        
        Response:
        {
            "success": bool,
            "message": str
        }
        """
        try:
            data = request.get_json()
            config = load_config()
            
            if 'openai' in data and data['openai']:
                config['api_keys']['openai'] = data['openai']
            
            if 'google' in data and data['google']:
                config['api_keys']['google'] = data['google']
            
            save_config(config)
            return jsonify({"success": True, "message": "API keys updated"})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    # =========================================================================
    # BACKUP & RESTORE ENDPOINTS
    # =========================================================================

    @app.route('/api/backup/conversations', methods=['GET'])
    def get_backup_conversations():
        """
        Get list of conversations for backup selection.
        
        Response:
        {
            "conversations": [
                {"id": str, "title": str, "timestamp": int, "pinned": bool}
            ]
        }
        """
        try:
            conversations = data.list_conversations()
            return jsonify({"conversations": conversations})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/backup/download', methods=['POST'])
    def download_backup():
        """
        Create and download a backup ZIP file.
        
        Request body:
        {
            "conversation_ids": list[str] | null  # null = all, [] = none
        }
        
        Response: ZIP file (application/zip)
        """
        from flask import Response
        
        try:
            req_data = request.get_json() or {}
            conversation_ids = req_data.get('conversation_ids')  # None = all
            
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
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/backup/validate', methods=['POST'])
    def validate_backup_file():
        """
        Validate an uploaded backup file.
        
        Request: multipart/form-data with 'file' field
        
        Response:
        {
            "valid": bool,
            "errors": list[str],
            "warnings": list[str],
            "manifest": dict | null,
            "files": list[str]
        }
        """
        try:
            if 'file' not in request.files:
                return jsonify({"valid": False, "errors": ["Tiedostoa ei ladattu"]}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({"valid": False, "errors": ["Tiedostoa ei valittu"]}), 400
            
            zip_bytes = file.read()
            result = backup.validate_backup(zip_bytes)
            
            return jsonify(result)
        except Exception as e:
            return jsonify({"valid": False, "errors": [str(e)]}), 500

    @app.route('/api/backup/restore', methods=['POST'])
    def restore_backup_file():
        """
        Restore from an uploaded backup file. OVERWRITES ALL DATA!
        
        Request: multipart/form-data with 'file' field
        
        Response:
        {
            "success": bool,
            "restored_files": list[str],
            "errors": list[str]
        }
        """
        try:
            if 'file' not in request.files:
                return jsonify({"success": False, "errors": ["Tiedostoa ei ladattu"]}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({"success": False, "errors": ["Tiedostoa ei valittu"]}), 400
            
            zip_bytes = file.read()
            result = backup.restore_backup(zip_bytes)
            
            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "errors": [str(e)]}), 500
