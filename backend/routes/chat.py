"""
Chat routes - Main AI conversation endpoint
"""

import logging
from flask import request, jsonify
import asyncio

logger = logging.getLogger(__name__)

from kortex import config, data
from kortex.ai import handler as ai_handler


def register_chat_routes(app):
    """Register chat-related endpoints"""
    
from backend.errors import handle_async_exceptions

# ... imports ...

def register_chat_routes(app):
    """Register chat-related endpoints"""
    
    @app.route('/api/chat', methods=['POST'])
    @handle_async_exceptions
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
        request_data = request.get_json()
        message = request_data.get('message', '')
        history = request_data.get('history', [])
        files = request_data.get('files', [])
        # Extract openrouter_reasoning_config if present
        openrouter_reasoning_config = request_data.get('openrouter_reasoning_config')
        
        if not message and not files:
            return jsonify({"error": "Message or files required"}), 400
        
        # Get config
        cfg = config.load_config()
        
        # ... (rest of the logic without outer try/except)
        
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
        
        # Initialize Scout for background analysis
        from kortex.ai.scout import scout_analyze
        
        # Load context for Scribe
        context = data.load_all_context()
        
        # Run Scout analysis in background (non-blocking for first message)
        scout_result = None
        try:
            scout_result = await scout_analyze(message, history)
            logger.info("Scout background: %s (%s%%)", scout_result['decision'], scout_result['confidence'])
        except Exception as e:
            logger.warning("Scout background analysis failed: %s", e)
        
        # Run Chat and Scribe SEQUENTIALLY
        loop = asyncio.get_event_loop()
        chat_result = await loop.run_in_executor(
            None, 
            ai_handler.get_ai_response, 
            message, history, model, provider, api_key, files, openrouter_reasoning_config
        )
        
        # Ensure we have valid response content for Scribe
        response_content = chat_result.get("response") or chat_result.get("error") or "(No response)"
        
        # Scribe Task
        scribe_updates = await scribe.analyze_and_update(message, response_content, context, history)
        
        # Update history with new messages
        user_message_entry = {"role": "user", "content": message}
        
        assistant_message_entry = {
            "role": "assistant",
            "content": response_content
        }
        
        # Preserve reasoning_details if present in the chat result from OpenRouter
        if "reasoning_details" in chat_result and chat_result["reasoning_details"]:
            assistant_message_entry["reasoning_details"] = chat_result["reasoning_details"]

        new_history = history + [user_message_entry, assistant_message_entry]
        
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
                from openai import OpenAI
                or_client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=cfg['api_keys'].get('openrouter')
                )
                
                title_prompt = f"""Generate a short, concise title (max 40 characters) for this conversation.
User message: {message}
AI response: {response_content[:200]}

Respond with ONLY the title, no quotes or extra text. Be specific and descriptive."""
                
                title_response = or_client.chat.completions.create(
                    model="google/gemini-3.1-flash-lite-preview",
                    messages=[{"role": "user", "content": title_prompt}],
                    max_tokens=50
                )
                
                if title_response.choices[0].message.content:
                    title = title_response.choices[0].message.content.strip()[:50]
                    logger.info("Generated title: '%s'", title)
                else:
                    title = message[:40] + "..." if len(message) > 40 else message
                    
            except Exception as e:
                logger.warning("Failed to generate title: %s", e)
                title = message[:40] + "..." if len(message) > 40 else message
            
        data.save_conversation(chat_id, new_history, title)
        
        # If AI only returned function calls without a conversational response,
        # generate a proper follow-up response
        if not chat_result.get('response') and chat_result.get('function_calls'):
            try:
                from openai import OpenAI
                or_client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=cfg['api_keys'].get('openrouter')
                )
                
                # Build a summary of what was updated
                updates_summary = ", ".join([fc['name'].replace('_', ' ') for fc in chat_result['function_calls']])
                
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

                followup_response = or_client.chat.completions.create(
                    model="google/gemini-3.1-flash-lite-preview",
                    messages=[{"role": "user", "content": followup_prompt}],
                    max_tokens=200
                )
                
                if followup_response.choices[0].message.content:
                    chat_result['response'] = followup_response.choices[0].message.content.strip()
                else:
                    chat_result['response'] = "Päivitin tiedot. Miten voin auttaa?"
                    
            except Exception as e:
                logger.warning("Follow-up generation failed: %s", e)
                chat_result['response'] = "Tiedot päivitetty! Onko muuta?"

        # Combine results
        response_data = chat_result
        response_data['chat_id'] = chat_id
        
        # Add Scout result for frontend
        if scout_result:
            response_data['scout'] = scout_result
        
        if scribe_updates:
            response_data['scribe_updates'] = scribe_updates
        
        return jsonify(response_data)
    
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
        except Exception:
            return jsonify({"success": False, "message": "Execution failed"}), 500

    @app.route('/api/chat/websearch', methods=['POST'])
    @handle_async_exceptions
    async def chat_websearch():
        """
        Web Search Pipeline - Scout -> Specialist -> Synthesizer
        
        Request body:
        {
            "message": str,
            "history": list[dict],
            "model": str,
            "provider": str,
            "reasoning_enabled": bool,
            "force_model": str (optional) - 'grok' or 'perplexity'
        }
        """
        request_data = request.get_json()
        message = request_data.get('message', '')
        history = request_data.get('history', [])
        reasoning_enabled = request_data.get('reasoning_enabled', False)
        force_model = request_data.get('force_model')  # User override
        
        if not message:
            return jsonify({"error": "Message required"}), 400
        
        # Get config
        cfg = config.load_config()
        
        # Use provided model/provider or defaults
        provider = request_data.get('provider', cfg['default_provider'])
        model = request_data.get('model', cfg['default_model'])
        
        # Load context
        context = data.load_all_context()
        
        # Run web search pipeline with Scout
        from kortex.ai.websearch import web_search_response
        
        result = await web_search_response(
            message=message,
            history=history,
            context=context,
            user_model=model,
            user_provider=provider,
            reasoning_enabled=reasoning_enabled,
            force_model=force_model
        )
        
        # Generate or use existing chat_id
        chat_id = request_data.get('chat_id')
        if not chat_id:
            chat_id = data.generate_chat_id()
        
        # Build response content with search metadata
        response_content = result.get('response', '')
        scout_info = result.get('scout', {})
        
        # Update history
        user_message_entry = {"role": "user", "content": message}
        assistant_message_entry = {
            "role": "assistant",
            "content": response_content,
            "web_search": {
                "type": result.get('search_type'),
                "specialist": result.get('specialist_model'),
                "sources": result.get('sources', []),
                "scout": scout_info
            }
        }
        
        new_history = history + [user_message_entry, assistant_message_entry]
        
        # Preserve existing title if conversation exists
        existing_title = None
        if chat_id:
            try:
                existing_conv = data.load_conversation(chat_id)
                if existing_conv:
                    existing_title = existing_conv.get('title')
            except Exception:
                pass
        
        # Generate title for new chats only
        title = existing_title or request_data.get('title', 'Web Search')
        if len(new_history) <= 2 and not existing_title:
            try:
                from openai import OpenAI
                or_client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=cfg['api_keys'].get('openrouter')
                )
                
                title_prompt = f"""Generate a short title (max 40 chars) for this web search conversation.
Query: {message}
Search type: {result.get('search_type')}
Respond with ONLY the title."""
                
                title_response = or_client.chat.completions.create(
                    model="google/gemini-3.1-flash-lite-preview",
                    messages=[{"role": "user", "content": title_prompt}],
                    max_tokens=50
                )
                if title_response.choices[0].message.content:
                    title = title_response.choices[0].message.content.strip()[:50]
            except Exception as e:
                logger.warning("Title generation failed: %s", e)
                title = f"🔍 {message[:35]}..."
        
        data.save_conversation(chat_id, new_history, title)
        
        return jsonify({
            "response": response_content,
            "chat_id": chat_id,
            "search_type": result.get('search_type'),
            "specialist_model": result.get('specialist_model'),
            "sources": result.get('sources', []),
            "scout": scout_info
        })

    @app.route('/api/chat/scout', methods=['POST'])
    @handle_async_exceptions
    async def chat_scout():
        """
        Scout Analysis - Check if message needs web search
        
        Request body:
        {
            "message": str,
            "history": list[dict] (optional)
        }
        
        Returns:
        {
            "decision": "NO_SEARCH" | "SUGGEST_SEARCH" | "FORCE_SEARCH",
            "confidence": 0-100,
            "search_type": "NEWS" | "RESEARCH",
            "reason": str,
            "recommended_model": str
        }
        """
        request_data = request.get_json()
        message = request_data.get('message', '')
        history = request_data.get('history', [])
        
        if not message:
            return jsonify({"error": "Message required"}), 400
        
        from kortex.ai.scout import scout_analyze
        
        result = await scout_analyze(message, history)
        
        return jsonify(result)
