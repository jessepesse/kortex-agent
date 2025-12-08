import google.generativeai as genai
import os
import json
import asyncio
import logging

from kortex.tools import TOOL_FUNCTIONS, GEMINI_TOOL_DEFINITIONS
from google.generativeai.types import generation_types

logger = logging.getLogger(__name__)

class ScribeService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.warning("ScribeService: No Google API Key found. Scribe disabled.")
            return
        
        genai.configure(api_key=self.api_key)
        
        # Define tools for the Scribe using Gemini-native format
        self.tools = GEMINI_TOOL_DEFINITIONS
        
        # Initialize Gemini 2.5 Flash Lite model
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-lite",
            tools=self.tools
        )

    def _build_system_prompt(self, context):
        """Build a system prompt with FULL context data."""
        prompt = """You are The Scribe, the ONLY system responsible for maintaining data in Kortex.
The main chat model does NOT have access to tools - you are the sole data handler.

Your goal: Keep all data files accurate and up-to-date based on conversations.

CURRENT DATA STATE:
"""
        # Include ALL data files with their full content
        for key, value in context.items():
            prompt += f"\n## {key.upper().replace('_', ' ')}\n"
            prompt += f"```json\n{json.dumps(value, indent=2)}\n```\n"

        prompt += """

INSTRUCTIONS:
1. Analyze the FULL conversation history for facts, updates, or changes.
2. When you find NEW or CORRECTED data, call the appropriate `update_*` tool immediately.
3. If NO data changes are needed, return "No updates".
4. DO NOT converse. DO NOT answer questions. ONLY update data or return "No updates".

Examples:
✅ "I moved to Berlin" → update_profile
✅ "My budget is 2000€" → update_finance  
✅ "I bought milk" → update_pantry_staples
❌ "What's my budget?" → No updates (this is a question, not new data)
"""
        return prompt

    async def analyze_and_update(self, message, ai_response, context, history=None):
        """
        Analyze the full conversation (with FULL history + context) and execute updates.
        Returns a list of success messages (e.g., "Updated profile").
        """
        if not self.api_key:
            return []

        logger.info("Scribe: Analyzing with full context...")
        
        try:
            system_prompt = self._build_system_prompt(context)
            
            # Build full prompt with history
            full_prompt = f"{system_prompt}\n\nCONVERSATION TO ANALYZE:\n"
            
            # Add conversation history if available
            if history:
                for msg in history[-10:]:  # Last 10 messages for context
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    full_prompt += f"{role.upper()}: {content}\n"
            
            # Add current exchange
            full_prompt += f"USER: {message}\n"
            full_prompt += f"ASSISTANT: {ai_response}\n"
            
            # Final instruction
            full_prompt += "\nBased on the conversation above, update any data files if new facts were established or changed. Call the appropriate tools."
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            # Use chat session WITH automatic function calling to allow proper function calls
            chat = self.model.start_chat(enable_automatic_function_calling=True)
            try:
                response = await loop.run_in_executor(
                    None, lambda: chat.send_message(full_prompt)
                )
            except generation_types.StopCandidateException as e:
                # Handle malformed function call gracefully
                logger.error(f"Scribe malformed function call: {e}")
                return []
            
            # Check if there were function calls
            updates = []
            if hasattr(response, 'candidates') and response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        fc = part.function_call
                        
                        # Convert MapComposite to dict (same approach as handler.py)
                        def convert_to_dict(obj):
                            if isinstance(obj, (str, int, float, bool, type(None))):
                                return obj
                            if hasattr(obj, 'items'):
                                return {k: convert_to_dict(v) for k, v in obj.items()}
                            if hasattr(obj, '__iter__'):
                                return [convert_to_dict(item) for item in obj]
                            return obj
                        
                        args = convert_to_dict(dict(fc.args))
                        
                        # Execute the function
                        from kortex.tools import TOOL_FUNCTIONS
                        if fc.name in TOOL_FUNCTIONS:
                            try:
                                result = TOOL_FUNCTIONS[fc.name](**args)
                                updates.append(f"✓ {fc.name}: {result}")
                                logger.info(f"Scribe executed: {fc.name}")
                            except Exception as e:
                                logger.error(f"Scribe failed to execute {fc.name}: {e}")
            
            if updates:
                logger.info(f"Scribe completed {len(updates)} updates")
            else:
                logger.debug("Scribe: No updates needed.")
                
            return updates

        except Exception as e:
            logger.error(f"Scribe Error: {e}")
            import traceback
            traceback.print_exc()
            return []
