"""
Chat routes - Main AI conversation endpoint
"""

from flask import request, jsonify
import asyncio

from kortex import config, data
from kortex.ai import handler as ai_handler


def register_chat_routes(app):
    """Register chat-related endpoints"""
    
    @app.route('/api/chat', methods=['POST'])
    async def chat():
        """
        Send a chat message to AI
        
        Request body:
        {
            "message": str,
            "history": list[dict],
            "model": str,
            "provider": str
        }
        """
        try:
            request_data = request.get_json()
            message = request_data.get('message', '')
            history = request_data.get('history', [])
            files = request_data.get('files', [])
            
            if not message and not files:
                return jsonify({"error": "Message or files required"}), 400
            
            # Get config
            cfg = config.load_config()
            
            # Use provided model/provider or defaults
            provider = request_data.get('provider', cfg['default_provider'])
            model = request_data.get('model', cfg['default_model'])
            
            # Get API key for provider
            api_key = cfg['api_keys'].get(provider)
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
            context = data.load_all_context()
            
            # Run Chat and Scribe SEQUENTIALLY
            loop = asyncio.get_event_loop()
            chat_result = await loop.run_in_executor(
                None, 
                ai_handler.get_ai_response, 
                message, history, model, provider, api_key, files
            )
            
            # Ensure we have valid response content for Scribe
            response_content = chat_result.get("response") or chat_result.get("error") or "(No response)"
            
            # Scribe Task
            scribe_updates = await scribe.analyze_and_update(message, response_content, context, history)
            
            # Update history with new messages
            new_history = history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": response_content}
            ]
            
            # Save conversation with AI-generated title
            existing_title = None
            if chat_id:
                try:
                    existing_conv = data.load_conversation(chat_id)
                    if existing_conv:
                        existing_title = existing_conv.get('title')
                except Exception:
                    pass
            
            title = existing_title or request_data.get('title', 'New Chat')
            
            # Generate title using AI for new chats
            if len(new_history) <= 2:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=cfg['api_keys'].get('google'))
                    
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
            
            # If AI only returned function calls without a conversational response,
            # generate a proper follow-up response
            if not chat_result.get('response') and chat_result.get('function_calls'):
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=cfg['api_keys'].get('google'))
                    
                    # Build a summary of what was updated
                    updates_summary = ", ".join([fc['name'].replace('_', ' ') for fc in chat_result['function_calls']])
                    
                    followup_model = genai.GenerativeModel('gemini-2.5-flash-lite')
                    followup_prompt = f"""The user said: "{message}"

You updated: {updates_summary}

IMPORTANT: Give a REAL, helpful response. This could be about ANYTHING:
- Technical (Linux, coding) → Give instructions/solutions
- Health/wellness → Actionable advice, empathy with substance  
- Projects/goals → Concrete next steps
- Emotions/life → Real perspectives, not just "ymmärrän"
- Finances → Practical guidance

Respond in Finnish. Be specific and genuinely helpful. 2-4 sentences.

DO NOT SAY:
- "Hyvä idea!" without WHY or next steps
- "Kerro lisää" - they already told you
- "Miten voin auttaa?" - help them NOW"""

                    followup_response = followup_model.generate_content(followup_prompt)
                    
                    if hasattr(followup_response, 'text') and followup_response.text:
                        chat_result['response'] = followup_response.text.strip()
                    else:
                        chat_result['response'] = "Päivitin tiedot. Miten voin auttaa?"
                        
                except Exception as e:
                    print(f"⚠️ Follow-up generation failed: {e}")
                    chat_result['response'] = "Tiedot päivitetty! Onko muuta?"

            # Combine results
            response_data = chat_result
            response_data['chat_id'] = chat_id
            
            if scribe_updates:
                response_data['scribe_updates'] = scribe_updates
            
            return jsonify(response_data)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/function-call/execute', methods=['POST'])
    def execute_function_call():
        """Execute a function call (after user approval)"""
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
