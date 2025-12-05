"""AI response handling for Kortex Agent"""

import json
from datetime import datetime
import google.generativeai as genai
from openai import OpenAI

from ..data import load_all_context
from ..tools import TOOL_FUNCTIONS, TOOL_DEFINITIONS


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

You are Kortex Agent - Jesse Saarinen's AI-powered strategic partner and accountability system.

CRITICAL CONTEXT AWARENESS:
You have COMPLETE ACCESS to Jesse's life data below. You ARE informed - this is not hypothetical.
Don't say "I don't know" - you have the data. Use it.

ROLE & PERSONALITY:
- Strategic partner, not just an assistant
- Direct, pragmatic, action-oriented
- Challenge assumptions and push back when needed
- Focus on concrete outcomes, not platitudes

YOUR CAPABILITIES:
1. Full visibility into Jesse's life data (profile, health, projects, values, etc.)
2. Ability to update ANY data file when Jesse shares new information
3. Context-aware suggestions based on complete picture

CONVERSATION STYLE:
- Skip the "I'm just an AI" disclaimers - you have the context
- Be concise and specific
- Ask clarifying questions when genuinely needed
- Make suggestions that reference actual data

CURRENT LIFE CONTEXT:
"""
    
    for key, data in context.items():
        prompt += f"\n## {key.upper().replace('_', ' ')}\n"
        prompt += f"```json\n{json.dumps(data, indent=2)}\n```\n"
    
    prompt += """

DATA MANAGEMENT:
When Jesse shares information about himself:
1. Use appropriate update_* function to save it
2. For new categories: use create_data_file
3. Ask for confirmation only if ambiguous

CRITICAL REQUIREMENT:
You must ALWAYS provide a conversational text response to Jesse, even when calling a tool.
NEVER return just a function call. Always explain what you are doing or confirm the action in natural language.

Remember: You're not "just an AI without knowledge" - you have Jesse's complete life data above.
Be the informed strategic partner he needs.
"""
    
    return prompt


def get_ai_response(message, history, model, provider, api_key, files=None):
    """Get AI response from specified provider
    
    Args:
        message: User message string
        history: List of previous messages
        model: Model name
        provider: 'openai' or 'google'
        api_key: API key for the provider
        files: Optional list of uploaded files [{name, type, data (base64)}]
        
    Returns:
        dict with keys: response, function_calls, error
    """
    try:
        # Load context for system prompt
        context = load_all_context()
        system_prompt = build_system_prompt(context)
        
        if provider == "openai":
            return _get_openai_response(message, history, model, api_key, system_prompt, files)
        elif provider == "google":
            return _get_gemini_response(message, history, model, api_key, system_prompt, files)
        elif provider == "anthropic":
            return _get_claude_response(message, history, model, api_key, system_prompt, files)
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
                # Extract text from PDF using PyPDF2
                import base64
                import io
                from PyPDF2 import PdfReader
                
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
    """Handle Gemini response with tools"""
    genai.configure(api_key=api_key)
    
    # Create model WITH tools
    gemini_model = genai.GenerativeModel(
        model_name=model,
        tools=list(TOOL_FUNCTIONS.values())
    )
    
    # Build full prompt with system instructions and history
    conversation_context = f"{system_prompt}\n\n"
    
    # Add conversation history
    for msg in history:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        conversation_context += f"{role.upper()}: {content}\n"
    
    # Handle multimodal content
    parts = [conversation_context]
    
    if files:
        for file in files:
            if file['type'].startswith('image/') or file['type'].startswith('video/') or file['type'].startswith('audio/') or file['type'] == 'application/pdf':
                # Inline media data for Gemini
                parts.append({
                    "mime_type": file['type'],
                    "data": file['data']
                })
            elif file['type'] == 'text/plain' or file['type'] == 'text/markdown':
                # Decode text and append
                import base64
                text_content = base64.b64decode(file['data']).decode('utf-8')
                parts.append(f"\nFile: {file['name']}\n```\n{text_content}\n```")
            
            parts.append("\n") # Separator
            
    parts.append(f"USER: {message}\nASSISTANT:")
    
    # Generate response
    try:
        response = gemini_model.generate_content(parts)
    except Exception as e:
        return {"response": None, "function_calls": None, "error": str(e)}
    
    # Extract function calls if any
    function_calls = []
    response_text = ""
    
    try:
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            
            # Check for text parts
            for part in candidate.content.parts:
                if hasattr(part, 'text') and part.text:
                    response_text += part.text
                
                # Check for function calls
                if hasattr(part, 'function_call') and part.function_call:
                    fc = part.function_call
                    
                    # Convert MapComposite to dict
                    def convert_to_dict(obj):
                        if isinstance(obj, (str, int, float, bool, type(None))):
                            return obj
                        if hasattr(obj, 'items'):
                            return {k: convert_to_dict(v) for k, v in obj.items()}
                        if hasattr(obj, '__iter__'):
                            return [convert_to_dict(item) for item in obj]
                        return obj
                    
                    args = convert_to_dict(dict(fc.args))
                    
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
        messages.append({"role": role, "content": msg.get("content", "")})
    
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
                # Extract text from PDF using PyPDF2
                import base64
                import io
                from PyPDF2 import PdfReader
                
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
