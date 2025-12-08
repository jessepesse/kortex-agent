"""
Council routes - Elite, Hive, and Mega council modes
"""

from flask import request, jsonify
import time
import random

from kortex import config, data


from backend.errors import handle_async_exceptions

# ... imports ...

def register_council_routes(app):
    """Register council/hive/mega endpoints"""
    
    def _generate_title(message, cfg, mode_name):
        """Helper to generate AI title for council chats"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=cfg['api_keys'].get('google'))
            
            title_model = genai.GenerativeModel('gemini-2.5-flash-lite')
            title_prompt = f"""Generate a short, concise title (max 40 characters) for this {mode_name} discussion.
User question: {message}

Respond with ONLY the title in Finnish, no quotes or extra text. Be specific and descriptive."""
            
            title_response = title_model.generate_content(title_prompt)
            
            if hasattr(title_response, 'text') and title_response.text:
                return title_response.text.strip()[:50]
        except Exception as e:
            print(f"⚠️ Failed to generate title: {e}")
        
        return message[:40] + "..." if len(message) > 40 else message

    @app.route('/api/council', methods=['POST'])
    @handle_async_exceptions
    async def council():
        """Trigger Council Mode: Query multiple models and synthesize"""
        request_data = request.get_json()
        message = request_data.get('message', '')
        history = request_data.get('history', [])
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        context = data.load_all_context()
        cfg = config.load_config()
        
        from kortex.ai.council import CouncilService
        service = CouncilService()
        result = await service.get_council_response(message, history, context)
        
        # Save conversation
        chat_id = request_data.get('chat_id') or f"{int(time.time())}_{hex(random.randint(0, 0xFFFFFFFF))[2:]}"
        
        existing_title = None
        try:
            existing_conv = data.load_conversation(chat_id)
            if existing_conv:
                existing_title = existing_conv.get('title')
        except Exception:
            pass
        
        title = existing_title or (
            _generate_title(message, cfg, "Elite Council") if len(history) <= 2 else 'New Chat'
        )
        
        new_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": result.get('chairman_response', ''), "council_type": "elite"}
        ]
        
        data.save_conversation(chat_id, new_history, title)
        
        # Include chat_id in response so frontend can track the conversation
        result['chat_id'] = chat_id
        return jsonify(result)

    @app.route('/api/hive', methods=['POST'])
    @handle_async_exceptions
    async def hive():
        """Trigger Hive Mode: 6 DeepSeek personas with specialized roles"""
        request_data = request.get_json()
        message = request_data.get('message', '')
        history = request_data.get('history', [])
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        context = data.load_all_context()
        cfg = config.load_config()
        
        from kortex.ai.hive import HiveService
        service = HiveService()
        result = await service.get_hive_response(message, history, context)
        
        # Save conversation
        chat_id = request_data.get('chat_id') or f"{int(time.time())}_{hex(random.randint(0, 0xFFFFFFFF))[2:]}"
        
        existing_title = None
        try:
            existing_conv = data.load_conversation(chat_id)
            if existing_conv:
                existing_title = existing_conv.get('title')
        except Exception:
            pass
        
        title = existing_title or (
            _generate_title(message, cfg, "Hive Council") if len(history) <= 2 else 'New Chat'
        )
        
        new_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": result.get('chairman_response', ''), "council_type": "hive"}
        ]
        
        data.save_conversation(chat_id, new_history, title)
        
        # Include chat_id in response so frontend can track the conversation
        result['chat_id'] = chat_id
        return jsonify(result)

    @app.route('/api/mega', methods=['POST'])
    @handle_async_exceptions
    async def mega():
        """Trigger MEGA Mode: Elite + Hive battle → Ultimate Chairman"""
        request_data = request.get_json()
        message = request_data.get('message', '')
        history = request_data.get('history', [])
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        context = data.load_all_context()
        cfg = config.load_config()
        
        from kortex.ai.mega import MegaCouncilService
        service = MegaCouncilService()
        result = await service.get_mega_response(message, history, context)
        
        # Save conversation
        chat_id = request_data.get('chat_id') or f"{int(time.time())}_{hex(random.randint(0, 0xFFFFFFFF))[2:]}"
        
        existing_title = None
        try:
            existing_conv = data.load_conversation(chat_id)
            if existing_conv:
                existing_title = existing_conv.get('title')
        except Exception:
            pass
        
        title = existing_title or (
            _generate_title(message, cfg, "MEGA Council") if len(history) <= 2 else 'New Chat'
        )
        
        new_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": result.get('mega_verdict', ''), "council_type": "mega"}
        ]
        
        data.save_conversation(chat_id, new_history, title)
        
        # Include chat_id in response so frontend can track the conversation
        result['chat_id'] = chat_id
        return jsonify(result)
