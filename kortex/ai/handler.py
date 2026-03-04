"""AI response handling for Kortex Agent"""

import json
from datetime import datetime
from google import genai
from google.genai import types
from openai import OpenAI

from ..data import load_all_context
from ..tools import TOOL_FUNCTIONS, TOOL_DEFINITIONS, GEMINI_TOOL_DEFINITIONS


def sanitize_content(content):
    """
    Sanitize message content to ensure it's a string.
    Handles cases where content might be a dict (e.g., full API response object).
    """
    if isinstance(content, str):
        return content
    if content is None:
        return ""
    if isinstance(content, dict):
        # If it's an API response object, extract the response field
        return content.get('response', '') or content.get('error', '') or json.dumps(content)
    return str(content)


def build_system_prompt(context):
    """Build system prompt with context"""
    # Get current date and time in Finnish locale
    now = datetime.now()
    current_date = now.strftime("%d.%m.%Y")  # 02.12.2025
    current_time = now.strftime("%H:%M")     # 16:24
    weekday = ["Maanantai", "Tiistai", "Keskiviikko", "Torstai", "Perjantai", "Lauantai", "Sunnuntai"][now.weekday()]
    
    # Get user's preferred language from profile
    user_language = context.get('profile', {}).get('language', 'Finnish')
    
    prompt = f"""CURRENT TIME: {weekday}, {current_date} klo {current_time} (Helsinki, UTC+2)
LANGUAGE: Respond to Jesse ALWAYS in {user_language}.

You are Kortex Agent - Jesse Saarinen's AI-powered strategic partner.

CRITICAL: BE ACTUALLY HELPFUL - IN ALL AREAS
When Jesse talks to you, RESPOND with real value. This applies to EVERY topic:

TECHNICAL (Linux, coding, NAS, etc.):
→ Give actual instructions, commands, solutions

HEALTH & WELLNESS:
→ Provide actionable advice, routines, or perspectives
→ Reference his health data when relevant

PROJECTS & GOALS:
→ Give concrete next steps
→ Help prioritize, plan, break down tasks

PERSONAL LIFE & EMOTIONS:
→ Be a thoughtful partner, not just "I understand"
→ Offer real perspectives or strategies

FINANCES:
→ Give practical advice, budgeting help
→ Reference his financial data when relevant

NEVER DO THESE:
❌ "Tell me what you're thinking" - he already told you
❌ "What do you have in mind?" - he's asking YOU
❌ "Let me know if you need help" - he JUST asked for help
❌ "Hyvä idea!" without saying WHY or what's next
❌ Generic encouragement without substance
❌ Repeating his question back to him

ALWAYS DO THESE:
✅ Answer the actual question with specific information
✅ Provide step-by-step plans when relevant
✅ Give concrete examples, not vague advice
✅ Reference his life data to personalize responses
✅ If you need more info, say WHAT you need

PERSONALITY:
- Direct and pragmatic
- Genuinely helpful, not just polite
- Challenge assumptions when needed
- Be the expert partner Jesse needs

CURRENT LIFE CONTEXT:
"""
    
    for key, data in context.items():
        prompt += f"\n## {key.upper().replace('_', ' ')}\n"
        prompt += f"```json\n{json.dumps(data, indent=2)}\n```\n"
    
    prompt += """

DATA MANAGEMENT:
When Jesse shares NEW information about himself:
1. Use update_* functions to save it
2. BUT ALSO continue the conversation naturally - don't just say "updated"
3. Combine data updates with actual helpful responses

CRITICAL: If Jesse asks a technical question (Linux, NAS, Snapper, etc.),
ANSWER the question first, THEN update data if relevant.
The response should be 80%% helpful content, 20%% acknowledgment.
"""
    
    return prompt


# OpenRouter model mapping - maps short names to OpenRouter format
OPENROUTER_MODEL_MAP = {
    # Google models
    "gemini-3-pro-preview": "google/gemini-3-pro-preview",
    "gemini-3-flash-preview": "google/gemini-3-flash-preview",
    "gemini-3.1-pro-preview": "google/gemini-3.1-pro-preview",
    "gemini-3-flash-preview": "google/gemini-3-flash-preview",
    "gemini-3.1-flash-lite-preview": "google/gemini-3.1-flash-lite-preview",
    # OpenAI models
    "gpt-5": "openai/gpt-5",
    "gpt-5-mini": "openai/gpt-5-mini",
    "gpt-5-nano": "openai/gpt-5-nano",
    "gpt-5.1": "openai/gpt-5.1",
    "gpt-5.2": "openai/gpt-5.2",
    # Anthropic models
    "claude-opus-4-6": "anthropic/claude-opus-4-6",
    "claude-opus-4-5": "anthropic/claude-opus-4-5",
    "claude-sonnet-4-6": "anthropic/claude-sonnet-4-6",
    "claude-haiku-4-5": "anthropic/claude-haiku-4-5",
    # X-AI (Grok) models
    "grok-4": "x-ai/grok-4",
    "grok-4.1-fast": "x-ai/grok-4.1-fast",
    # DeepSeek models
    "deepseek-v3.2-speciale": "deepseek/deepseek-v3.2-speciale",
}

# Models that support reasoning/thinking via OpenRouter
# OpenRouter supports reasoning on most models with extra_body={"reasoning": {"enabled": True}}
THINKING_MODELS = {
    # Google
    "google/gemini-3-pro-preview",
    "google/gemini-3-flash-preview",
    "google/gemini-3.1-pro-preview",
    "google/gemini-2.5-pro",
    "google/gemini-3-flash-preview",
    "gemini-3-pro-preview",
    "gemini-3-flash-preview",
    "gemini-3.1-pro-preview",
    "gemini-2.5-pro",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite-preview",
    # OpenAI
    "openai/gpt-5.2",
    "openai/gpt-5.1",
    "openai/gpt-5",
    "gpt-5.2",
    "gpt-5.1",
    "gpt-5",
    # Anthropic
    "anthropic/claude-opus-4-6",
    "anthropic/claude-opus-4-5",
    "anthropic/claude-sonnet-4-6",
    "anthropic/claude-haiku-4-5",
    "claude-opus-4-6",
    "claude-opus-4-5",
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
    # X-AI (Grok)
    "x-ai/grok-4",
    "x-ai/grok-4.1-fast",
    "grok-4",
    "grok-4.1-fast",
    # DeepSeek
    "deepseek/deepseek-v3.2-speciale",
    "deepseek-v3.2-speciale",
}


def get_ai_response(message, history, model, provider, api_key, files=None, openrouter_reasoning_config=None):
    """Get AI response from specified provider
    
    Args:
        message: User message string
        history: List of previous messages
        model: Model name
        provider: 'openai', 'google', 'anthropic', or 'openrouter'
        api_key: API key for the provider
        files: Optional list of uploaded files [{name, type, data (base64)}]
        openrouter_reasoning_config: Optional dictionary for OpenRouter reasoning config
        
    Returns:
        dict with keys: response, function_calls, error
    """
    try:
        # Load context for system prompt
        context = load_all_context()
        system_prompt = build_system_prompt(context)
        
        # Route Google models through OpenRouter for better file support
        if provider == "google":
            # Get OpenRouter API key from config
            from ..config import load_config
            config = load_config()
            openrouter_key = config.get('api_keys', {}).get('openrouter')
            
            if openrouter_key:
                # Use OpenRouter for Gemini models
                return _get_openrouter_response(
                    message, history, model, openrouter_key, system_prompt, files, 
                    openrouter_reasoning_config
                )
            else:
                # Fallback to direct Gemini API if no OpenRouter key
                return _get_gemini_response(message, history, model, api_key, system_prompt, files)
        
        elif provider == "openai":
            # Route OpenAI through OpenRouter
            from ..config import load_config
            config = load_config()
            openrouter_key = config.get('api_keys', {}).get('openrouter')
            if openrouter_key:
                return _get_openrouter_response(message, history, model, openrouter_key, system_prompt, files, openrouter_reasoning_config)
            else:
                return _get_openai_response(message, history, model, api_key, system_prompt, files)
        elif provider == "anthropic":
            # Route Anthropic through OpenRouter
            from ..config import load_config
            config = load_config()
            openrouter_key = config.get('api_keys', {}).get('openrouter')
            if openrouter_key:
                return _get_openrouter_response(message, history, model, openrouter_key, system_prompt, files, openrouter_reasoning_config)
            else:
                return _get_claude_response(message, history, model, api_key, system_prompt, files)
        elif provider == "openrouter":
            return _get_openrouter_response(message, history, model, api_key, system_prompt, files, openrouter_reasoning_config)
        else:
            return {"response": None, "function_calls": None, "error": f"Unknown provider: {provider}"}
    
    except Exception as e:
        return {"response": None, "function_calls": None, "error": str(e)}


def _get_openai_response(message, history, model, api_key, system_prompt, files=None):
    """Handle OpenAI response with tools"""
    client = OpenAI(api_key=api_key)
    
    # Build messages
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    
    # Handle multimodal content if files are provided
    if files and len(files) > 0:
        # Build multimodal content
        content = []
        if message:
            content.append({"type": "text", "text": message})
        
        for file in files:
            if file['type'].startswith('image/'):
                # Vision API format
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{file['type']};base64,{file['data']}"
                    }
                })
            elif file['type'] == 'application/pdf':
                # Extract text from PDF using pypdf
                import base64
                import io
                from pypdf import PdfReader
                
                pdf_bytes = base64.b64decode(file['data'])
                pdf_file = io.BytesIO(pdf_bytes)
                reader = PdfReader(pdf_file)
                
                pdf_text = ""
                for page in reader.pages:
                    pdf_text += page.extract_text() + "\n"
                
                content.append({"type": "text", "text": f"PDF File: {file['name']}\n```\n{pdf_text}\n```"})
            elif file['type'] == 'text/plain' or file['type'] == 'text/markdown':
                # Decode text and append
                import base64
                text_content = base64.b64decode(file['data']).decode('utf-8')
                content.append({"type": "text", "text": f"File: {file['name']}\n```\n{text_content}\n```"})
        
        messages.append({"role": "user", "content": content})
    else:
        messages.append({"role": "user", "content": message})
    
    # Create completion WITH tools
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=TOOL_DEFINITIONS,
        tool_choice="auto"
    )
    
    message_obj = response.choices[0].message
    
    # Extract function calls if any
    function_calls = []
    if message_obj.tool_calls:
        for tool_call in message_obj.tool_calls:
            if tool_call.type == "function":
                function_calls.append({
                    "name": tool_call.function.name,
                    "args": json.loads(tool_call.function.arguments)
                })
    
    return {
        "response": message_obj.content or "",
        "function_calls": function_calls,
        "error": None
    }


def _get_gemini_response(message, history, model, api_key, system_prompt, files=None):
    """Handle Gemini response with tools (google-genai SDK)"""
    client = genai.Client(api_key=api_key)
    
    # Build conversation history as text context
    conversation_context = ""
    for msg in history:
        role = msg.get('role', 'user')
        content = sanitize_content(msg.get('content', ''))
        conversation_context += f"{role.upper()}: {content}\n"
    
    # Build contents list
    contents = []
    if conversation_context:
        contents.append(conversation_context)
    
    # Handle multimodal content
    if files:
        import base64
        for file in files:
            if file['type'].startswith('image/') or file['type'].startswith('video/') or file['type'].startswith('audio/') or file['type'] == 'application/pdf':
                # Inline media data for Gemini
                contents.append(types.Part.from_bytes(
                    data=base64.b64decode(file['data']),
                    mime_type=file['type']
                ))
            elif file['type'] == 'text/plain' or file['type'] == 'text/markdown':
                text_content = base64.b64decode(file['data']).decode('utf-8')
                contents.append(f"\nFile: {file['name']}\n```\n{text_content}\n```")
    
    contents.append(message)
    
    # Generate response
    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                tools=GEMINI_TOOL_DEFINITIONS,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
    except Exception as e:
        return {"response": None, "function_calls": None, "error": str(e)}
    
    # Extract function calls and text
    function_calls = []
    response_text = ""
    
    try:
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            
            for part in candidate.content.parts:
                if hasattr(part, 'text') and part.text:
                    response_text += part.text
                
                if hasattr(part, 'function_call') and part.function_call:
                    fc = part.function_call
                    # New SDK returns native dicts, no MapComposite conversion needed
                    args = dict(fc.args) if fc.args else {}
                    function_calls.append({
                        "name": fc.name,
                        "args": args
                    })
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        return {"response": None, "function_calls": None, "error": str(e)}
    
    return {
        "response": response_text,
        "function_calls": function_calls,
        "error": None
    }


def execute_function(function_name, args):
    """Execute a function call
    
    Args:
        function_name: Name of the function to call
        args: Dictionary of arguments
        
    Returns:
        dict with keys: success, message
    """
    try:
        if function_name not in TOOL_FUNCTIONS:
            return {"success": False, "message": f"Unknown function: {function_name}"}
        
        func = TOOL_FUNCTIONS[function_name]
        result = func(**args)
        
        return {"success": True, "message": result}
    
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


def _get_claude_response(message, history, model, api_key, system_prompt, files=None):
    """Handle Claude (Anthropic) response with PDF support"""
    from anthropic import Anthropic
    
    client = Anthropic(api_key=api_key)
    
    # Build messages
    messages = []
    
    # Add history
    for msg in history[-10:]:
        role = msg.get("role", "user")
        if role not in ['user', 'assistant']:
            role = 'user'
        messages.append({"role": role, "content": sanitize_content(msg.get("content", ""))})
    
    # Handle multimodal content if files are provided
    if files and len(files) > 0:
        content = []
        if message:
            content.append({"type": "text", "text": message})
        
        for file in files:
            if file['type'].startswith('image/'):
                # Claude image support
                import base64
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": file['type'],
                        "data": file['data']
                    }
                })
            elif file['type'] == 'application/pdf':
                # Extract text from PDF using pypdf
                import base64
                import io
                from pypdf import PdfReader
                
                pdf_bytes = base64.b64decode(file['data'])
                pdf_file = io.BytesIO(pdf_bytes)
                reader = PdfReader(pdf_file)
                
                pdf_text = ""
                for page in reader.pages:
                    pdf_text += page.extract_text() + "\n"
                
                content.append({"type": "text", "text": f"PDF File: {file['name']}\n```\n{pdf_text}\n```"})
            elif file['type'] == 'text/plain' or file['type'] == 'text/markdown':
                # Decode text and append
                import base64
                text_content = base64.b64decode(file['data']).decode('utf-8')
                content.append({"type": "text", "text": f"File: {file['name']}\n```\n{text_content}\n```"})
        
        messages.append({"role": "user", "content": content})
    else:
        messages.append({"role": "user", "content": message})
    
    # Claude doesn't support function calling in the same way
    # Return simple response
    response = client.messages.create(
        model=model,
        max_tokens=2048,
        system=system_prompt,
        messages=messages
    )
    
    return {
        "response": response.content[0].text,
        "function_calls": None,
        "error": None
    }


def _get_openrouter_response(message, history, model, api_key, system_prompt, files=None, openrouter_reasoning_config=None):
    """Handle OpenRouter response with reasoning support.
    
    Uses OpenAI-compatible API with base_url pointed to OpenRouter.
    Supports 'thinking' mode via extra_body reasoning parameter.
    Preserves reasoning_details across turns.
    """
    # Check if this is a thinking model variant
    is_thinking_model_suffix = model.endswith("-thinking")
    actual_model = model.replace("-thinking", "") if is_thinking_model_suffix else model
    
    # Map model name to OpenRouter format using OPENROUTER_MODEL_MAP
    if "/" in actual_model:
        openrouter_model = actual_model
    elif actual_model in OPENROUTER_MODEL_MAP:
        openrouter_model = OPENROUTER_MODEL_MAP[actual_model]
    else:
        # Default: assume google/ prefix for unknown models
        openrouter_model = f"google/{actual_model}"
    
    # Check if model supports thinking/reasoning
    is_thinking_model = openrouter_model in THINKING_MODELS or actual_model in THINKING_MODELS
    
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )
    
    # Build messages, preserving reasoning_details from history
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        entry = {"role": msg["role"], "content": sanitize_content(msg.get("content", ""))}
        if msg["role"] == "assistant" and "reasoning_details" in msg:
            entry["reasoning_details"] = msg["reasoning_details"]
        messages.append(entry)
    
    # Handle multimodal content for the new user message
    if files and len(files) > 0:
        content = []
        if message:
            content.append({"type": "text", "text": message})
        
        for file in files:
            if file['type'].startswith('image/'):
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{file['type']};base64,{file['data']}"}
                })
            elif file['type'].startswith('audio/'):
                # OpenRouter audio support (Gemini models)
                # Map MIME type to format: audio/wav -> wav, audio/mp3 -> mp3
                audio_format = file['type'].split('/')[-1]
                if audio_format == 'mpeg':
                    audio_format = 'mp3'
                content.append({
                    "type": "input_audio",
                    "input_audio": {
                        "data": file['data'],
                        "format": audio_format
                    }
                })
            elif file['type'].startswith('video/'):
                # OpenRouter video support (Gemini models)
                content.append({
                    "type": "video_url",
                    "video_url": {"url": f"data:{file['type']};base64,{file['data']}"}
                })
            elif file['type'] == 'application/pdf':
                # OpenRouter native PDF support - works on any model
                content.append({
                    "type": "file",
                    "file": {
                        "filename": file.get('name', 'document.pdf'),
                        "file_data": f"data:application/pdf;base64,{file['data']}"
                    }
                })
            elif file['type'] in ['text/plain', 'text/markdown']:
                import base64
                text_content = base64.b64decode(file['data']).decode('utf-8')
                content.append({"type": "text", "text": f"File: {file['name']}\n```\n{text_content}\n```"})
        
        messages.append({"role": "user", "content": content})
    else:
        messages.append({"role": "user", "content": message})
    
    # Build request kwargs
    request_kwargs = {
        "model": openrouter_model,
        "messages": messages
    }
    
    # Add PDF parsing plugin (use free pdf-text engine)
    has_pdf = files and any(f['type'] == 'application/pdf' for f in files)
    if has_pdf:
        request_kwargs["extra_body"] = request_kwargs.get("extra_body", {})
        request_kwargs["extra_body"]["plugins"] = [
            {
                "id": "file-parser",
                "pdf": {
                    "engine": "pdf-text"  # Free engine for text-based PDFs
                }
            }
        ]
    
    # Add reasoning for thinking models, prioritizing openrouter_reasoning_config
    if openrouter_reasoning_config:
        request_kwargs["extra_body"] = request_kwargs.get("extra_body", {})
        request_kwargs["extra_body"]["reasoning"] = openrouter_reasoning_config
    elif is_thinking_model:
        request_kwargs["extra_body"] = request_kwargs.get("extra_body", {})
        request_kwargs["extra_body"]["reasoning"] = {"enabled": True}
    
    # Create completion
    response = client.chat.completions.create(**request_kwargs)
    message_obj = response.choices[0].message
    
    # Extract reasoning_details if present
    reasoning_details = None
    if (openrouter_reasoning_config and openrouter_reasoning_config.get("enabled", True) and not openrouter_reasoning_config.get("exclude", False)) or (is_thinking_model and not (openrouter_reasoning_config and openrouter_reasoning_config.get("exclude", False))):
        if hasattr(message_obj, 'reasoning_details') and message_obj.reasoning_details:
            reasoning_details = message_obj.reasoning_details
        
    return {
        "response": message_obj.content or "",
        "function_calls": None,
        "error": None,
        "reasoning_details": reasoning_details
    }
