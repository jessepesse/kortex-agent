from openai import OpenAI
import os
import json
import asyncio
import logging

from kortex.tools import TOOL_FUNCTIONS, TOOL_DEFINITIONS

logger = logging.getLogger(__name__)

class ScribeService:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            logger.warning("ScribeService: No OpenRouter API Key found. Scribe disabled.")
            return
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )
        
        # Use OpenAI-style tool definitions
        self.tools = TOOL_DEFINITIONS

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
            
            # Build messages for OpenAI API
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history if available
            if history:
                for msg in history[-10:]:  # Last 10 messages for context
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    # Sanitize content if it's a dict
                    if isinstance(content, dict):
                        content = content.get('response', str(content))
                    messages.append({"role": role, "content": content})
            
            # Add current exchange as final user message
            final_prompt = f"""USER: {message}
ASSISTANT: {ai_response}

Based on the conversation above, update any data files if new facts were established or changed. Call the appropriate tools. If no updates needed, just respond with "No updates"."""
            messages.append({"role": "user", "content": final_prompt})
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            def make_request():
                return self.client.chat.completions.create(
                    model="google/gemini-3.1-flash-lite-preview",
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto"
                )
            
            response = await loop.run_in_executor(None, make_request)
            
            # Check if there were tool calls
            updates = []
            choice = response.choices[0]
            
            if choice.message.tool_calls:
                for tool_call in choice.message.tool_calls:
                    func_name = tool_call.function.name
                    try:
                        args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        logger.error(f"Scribe failed to parse args for {func_name}")
                        continue
                    
                    # Execute the function
                    if func_name in TOOL_FUNCTIONS:
                        try:
                            result = TOOL_FUNCTIONS[func_name](**args)
                            updates.append(f"✓ {func_name}: {result}")
                            logger.info(f"Scribe executed: {func_name}")
                        except Exception as e:
                            logger.error(f"Scribe failed to execute {func_name}: {e}")
            
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
