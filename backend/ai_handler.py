#!/usr/bin/env python3
"""
AI Handler - Extracted from main.py for Flask backend
Handles all AI interactions, function calling, and data management
"""

import json
from google import genai
from google.genai import types
from openai import OpenAI
from pathlib import Path

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
CONFIG_FILE = Path(__file__).parent.parent / "config.json"


# =============================================================================
# DATA MANAGEMENT
# =============================================================================

def get_all_json_files():
    """Dynamically scan the data directory for all JSON files."""
    DATA_DIR.mkdir(exist_ok=True)
    json_files = [f.name for f in DATA_DIR.glob("*.json")]
    json_files.sort()
    return json_files


def load_json_file(filename):
    """Load a JSON file from the data directory."""
    filepath = DATA_DIR / filename
    DATA_DIR.mkdir(exist_ok=True)
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        default_data = {}
        with open(filepath, 'w') as f:
            json.dump(default_data, f, indent=2)
        return default_data
    except json.JSONDecodeError:
        print(f"Warning: Could not parse {filename}. Using empty dict.")
        return {}


def save_json_file(filename, data):
    """Save data to a JSON file in the data directory."""
    filepath = DATA_DIR / filename
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    return f"✓ Updated {filename}"


def load_all_context():
    """Dynamically load all JSON files from the data directory."""
    context = {}
    json_files = get_all_json_files()
    
    for filename in json_files:
        key = filename.replace('.json', '')
        context[key] = load_json_file(filename)
    
    return context


# =============================================================================
# FUNCTION CALLING TOOLS
# =============================================================================

def update_profile(data: dict) -> str:
    """Update profile information"""
    existing = load_json_file("profile.json")
    merged = {**existing, **data}
    save_json_file("profile.json", merged)
    return "Profile updated"


def update_values(data: dict) -> str:
    """Update core values and anti-values"""
    existing = load_json_file("values.json")
    merged = {**existing, **data}
    save_json_file("values.json", merged)
    return "Values updated"


def update_health(data: dict) -> str:
    """Update health metrics"""
    existing = load_json_file("health.json")
    merged = {**existing, **data}
    save_json_file("health.json", merged)
    return "Health updated"


def update_tech_inventory(data: dict) -> str:
    """Update tech inventory"""
    existing = load_json_file("tech_inventory.json")
    merged = {**existing, **data}
    save_json_file("tech_inventory.json", merged)
    return "Tech inventory updated"


def update_active_projects(data: dict) -> str:
    """Update active projects"""
    existing = load_json_file("active_projects.json")
    merged = {**existing, **data}
    save_json_file("active_projects.json", merged)
    return "Projects updated"


def update_routines(data: dict) -> str:
    """Update routines"""
    existing = load_json_file("routines.json")
    merged = {**existing, **data}
    save_json_file("routines.json", merged)
    return "Routines updated"


def update_pantry_staples(data: dict) -> str:
    """Update pantry inventory"""
    existing = load_json_file("pantry_staples.json")
    merged = {**existing, **data}
    save_json_file("pantry_staples.json", merged)
    return "Pantry updated"


def update_meal_rotation(data: dict) -> str:
    """Update meal rotation"""
    existing = load_json_file("meal_rotation.json")
    merged = {**existing, **data}
    save_json_file("meal_rotation.json", merged)
    return "Meals updated"


def update_finance(data: dict) -> str:
    """Update finance data"""
    existing = load_json_file("finance.json")
    merged = {**existing, **data}
    save_json_file("finance.json", merged)
    return "Finance updated"


def create_data_file(filename: str, initial_data: dict, description: str = "") -> str:
    """Create a new JSON data file"""
    if not filename.endswith('.json'):
        filename = f"{filename}.json"
    
    if '/' in filename or '\\' in filename or '..' in filename:
        return f"Error: Invalid filename"
    
    filepath = DATA_DIR / filename
    if filepath.exists():
        return f"Error: File exists"
    
    try:
        with open(filepath, 'w') as f:
            json.dump(initial_data, f, indent=2)
        return f"✓ Created {filename}"
    except Exception as e:
        return f"Error: {str(e)}"


# Tool functions mapping
TOOL_FUNCTIONS = {
    "update_profile": update_profile,
    "update_values": update_values,
    "update_health": update_health,
    "update_tech_inventory": update_tech_inventory,
    "update_active_projects": update_active_projects,
    "update_routines": update_routines,
    "update_pantry_staples": update_pantry_staples,
    "update_meal_rotation": update_meal_rotation,
    "update_finance": update_finance,
    "create_data_file": create_data_file,
}


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

def build_system_prompt(context):
    """Build system prompt with context"""
    prompt = """You are a pragmatic, no-nonsense strategic partner for Jesse Saarinen.

ROLE & TONE:
- Direct and pragmatic
- Focus on actionable insights
- Challenge assumptions when needed

CURRENT LIFE CONTEXT:
"""
    
    for key, data in context.items():
        prompt += f"\n## {key.upper().replace('_', ' ')}\n"
        prompt += f"```json\n{json.dumps(data, indent=2)}\n```\n"
    
    prompt += """

DATA MANAGEMENT:
1. Update existing: Use update_* functions with complete data
2. Create new: Use create_data_file for new tracking categories

Be concise. Make suggestions specific and actionable.
"""
    
    return prompt


# =============================================================================
# AI RESPONSE HANDLER
# =============================================================================

def get_ai_response(message, history, model, provider, api_key):
    """
    Get AI response with function calling support
    
    Returns:
        dict: {
            "response": str or None,
            "function_calls": list or None,
            "error": str or None
        }
    """
    try:
        # Load context and build prompt
        context = load_all_context()
        system_prompt = build_system_prompt(context)
        
        # Prepare messages
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})
        
        if provider == "openai":
            return _get_openai_response(messages, model, api_key)
        else:  # gemini
            return _get_gemini_response(message, model, api_key)
            
    except Exception as e:
        return {"response": None, "function_calls": None, "error": str(e)}


def _get_openai_response(messages, model, api_key):
    """Handle OpenAI API call"""
    client = OpenAI(api_key=api_key)
    
    # Convert tools to OpenAI format
    openai_tools = []
    for func_name, tool_func in TOOL_FUNCTIONS.items():
        openai_tools.append({
            "type": "function",
            "function": {
                "name": func_name,
                "description": tool_func.__doc__ or "",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "data": {"type": "object"}
                    }
                }
            }
        })
    
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=openai_tools
    )
    
    message = response.choices[0].message
    response_text = message.content
    
    # Check for function calls
    function_calls = None
    if message.tool_calls:
        function_calls = []
        for tool_call in message.tool_calls:
            try:
                args = json.loads(tool_call.function.arguments)
            except:
                args = {}
            
            function_calls.append({
                "name": tool_call.function.name,
                "args": args,
                "id": tool_call.id
            })
    
    return {
        "response": response_text,
        "function_calls": function_calls,
        "error": None
    }


def _get_gemini_response(message, model, api_key):
    """Handle Gemini API call (google-genai SDK)"""
    client = genai.Client(api_key=api_key)
    
    response = client.models.generate_content(
        model=model,
        contents=message,
        config=types.GenerateContentConfig(
            tools=list(TOOL_FUNCTIONS.values()),
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )
    
    # Check for function calls FIRST
    has_function_calls = False
    if hasattr(response, 'candidates') and response.candidates:
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'function_call') and part.function_call:
                has_function_calls = True
                break
    
    if has_function_calls:
        function_calls = []
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'function_call') and part.function_call:
                fc = part.function_call
                # New SDK returns native dicts
                args = dict(fc.args) if fc.args else {}
                function_calls.append({
                    "name": fc.name,
                    "args": args
                })
        
        return {
            "response": None,
            "function_calls": function_calls,
            "error": None
        }
    
    elif hasattr(response, 'text') and response.text:
        return {
            "response": response.text,
            "function_calls": None,
            "error": None
        }
    
    else:
        return {
            "response": None,
            "function_calls": None,
            "error": "No response from AI"
        }


def execute_function(function_name, args):
    """
    Execute a function call
    
    Returns:
        dict: {"success": bool, "message": str}
    """
    try:
        if function_name in TOOL_FUNCTIONS:
            result = TOOL_FUNCTIONS[function_name](**args)
            return {"success": True, "message": result}
        else:
            return {"success": False, "message": f"Unknown function: {function_name}"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}
