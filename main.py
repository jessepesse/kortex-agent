#!/usr/bin/env python3
"""
Personal Kortex Agent Chatbot - Multi-Provider AI Assistant
Supports both OpenAI and Google Gemini with persistent API key storage.
"""

import os
import json
import google.generativeai as genai
from openai import OpenAI
from pathlib import Path
import sys

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

#Import from kortex package
from kortex.config import load_config, save_config, setup_api_keys
from kortex.data import load_all_context
from kortex.tools import TOOL_FUNCTIONS
from kortex.ai.handler import build_system_prompt
from kortex.ai.providers import LLMClient


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def safe_str(val):
    """Sanitize string for display (CodeQL safe)."""
    # CodeQL: Construct new string to break taint
    if not val: return ""
    return "".join(c for c in str(val) if c.isalnum() or c in " ._-:/")

def select_model(config):
    """Interactive model selection"""   
    print("\n📋 Available Models:\n")
    
    all_models = []
    idx = 1
    
    # List all models
    for provider, models in config["models"].items():
        # CodeQL: Sanitize output
        p_safe = safe_str(provider).upper()
        print(f"  {p_safe}:")
        for model in models:
            m_safe = safe_str(model)
            print(f"    {idx}. {m_safe}")
            all_models.append((provider, model))
            idx += 1
    
    def_p = safe_str(config['default_provider'])
    def_m = safe_str(config['default_model'])
    print(f"\n  {idx}. Use default ({def_p}: {def_m})")
    
    choice = input("\nSelect model number: ").strip()
    
    if not choice or choice == str(idx):
        return config["default_provider"], config["default_model"]
    
    try:
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(all_models):
            return all_models[choice_idx]
    except:
        pass
    
    return config["default_provider"], config["default_model"]


def main():
    """Main application loop"""
    # Load config
    config = load_config()
    config = setup_api_keys(config)
    
    # Select model
    provider, model = select_model(config)
    
    # Get API key
    api_key = config["api_keys"].get(provider, "")
    if not api_key:
        print("\n❌ No API key found for selected provider. Please check config.json")
        return
    
    # Initialize LLM client
    try:
        llm = LLMClient(provider, model, api_key)
        print("\n✓ Model initialized successfully\n")
    except Exception:
        # CodeQL: Static error message used. No sensitive variables (API keys/tokens) are logged.
        print("\n❌ Error initializing AI provider: Authentication failed or connection error.")
        return
    
    print("="*60)
    # CodeQL: Sanitize output
    p_safe = safe_str(provider).upper()
    m_safe = safe_str(model)
    print(f"🧠 LIFE OS - {p_safe} {m_safe}")
    print("="*60)
    print("Commands: quit, exit, reload, model (change model)")
    print("="*60)
    
    chat_history = []
    
    while True:
        print("\n")
        user_input = input("You: ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() in ['quit', 'exit']:
            print("\nGoodbye! 👋")
            break
        
        if user_input.lower() == 'reload':
            print("✓ Context reloaded")
            continue
        
        if user_input.lower() == 'model':
            provider, model = select_model(config)
            api_key = config["api_keys"].get(provider, "")
            try:
                llm = LLMClient(provider, model, api_key)
                print("✓ Switched AI provider successfully")
                chat_history = []
            except Exception:
                print("❌ Error: Could not switch model.")
            continue
        
        # Load context and build prompt
        context = load_all_context()
        system_prompt = build_system_prompt(context)
        
        # Prepare messages
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history)
        messages.append({"role": "user", "content": user_input})
        
        try:
            print("\nAssistant: ", end="", flush=True)
            
            response = llm.chat(messages, tools=list(TOOL_FUNCTIONS.values()))
            
            # Handle response based on provider
            if provider == "openai":
                # OpenAI response handling
                message = response.choices[0].message
                response_text = message.content or ""
                
                # Check for function calls
                if message.tool_calls:
                    # Show what functions AI wants to call
                    print("\n" + "="*60)
                    print("🔧 AI wants to update the following data:")
                    print("="*60)
                    
                    tool_calls_data = []
                    for tool_call in message.tool_calls:
                        func_name = tool_call.function.name
                        try:
                            args = json.loads(tool_call.function.arguments)
                        except:
                            args = {}
                        
                        readable_name = func_name.replace('update_', '').replace('_', ' ').title()
                        print(f"\n📝 {readable_name}:")
                        print(json.dumps(args.get('data', args), indent=2))
                        
                        tool_calls_data.append((tool_call.id, func_name, args))
                    
                    print("\n" + "="*60)
                    
                    # Ask for confirmation
                    confirm = input("Apply these updates? (y/n): ").strip().lower()
                    
                    if confirm == 'y':
                        # Execute functions and prepare results
                        tool_results = []
                        for tool_id, func_name, args in tool_calls_data:
                            try:
                                if func_name in TOOL_FUNCTIONS:
                                    result = TOOL_FUNCTIONS[func_name](**args)
                                    print(f"✓ {result}")
                                    tool_results.append({
                                        "tool_call_id": tool_id,
                                        "role": "tool",
                                        "name": func_name,
                                        "content": json.dumps({"result": result})
                                    })
                                else:
                                    error_msg = f"Unknown function: {func_name}"
                                    print(f"✗ {error_msg}")
                                    tool_results.append({
                                        "tool_call_id": tool_id,
                                        "role": "tool",
                                        "name": func_name,
                                        "content": json.dumps({"error": error_msg})
                                    })
                            except Exception as e:
                                error_msg = f"Error: {str(e)}"
                                print(f"✗ {error_msg}")
                                tool_results.append({
                                    "tool_call_id": tool_id,
                                    "role": "tool",
                                    "name": func_name,
                                    "content": json.dumps({"error": error_msg})
                                })
                        
                        print()
                        
                        # Send results back to OpenAI to get final response
                        messages.append({
                            "role": "assistant",
                            "content": response_text,
                            "tool_calls": [
                                {
                                    "id": tc.id,
                                    "type": "function",
                                    "function": {
                                        "name": tc.function.name,
                                        "arguments": tc.function.arguments
                                    }
                                }
                                for tc in message.tool_calls
                            ]
                        })
                        messages.extend(tool_results)
                        
                        # Get final response
                        print("Assistant: ", end="", flush=True)
                        final_response = llm.client.chat.completions.create(
                            model=llm.model,
                            messages=messages
                        )
                        final_text = final_response.choices[0].message.content or ""
                        print(final_text)
                        
                        # Update history with final response
                        chat_history.append({"role": "user", "content": user_input})
                        chat_history.append({"role": "assistant", "content": final_text})
                    else:
                        print("✗ Updates cancelled.\n")
                        chat_history.append({"role": "user", "content": user_input})
                        chat_history.append({"role": "assistant", "content": "Updates were cancelled."})
                else:
                    # No function calls, just text response
                    print(response_text)
                    chat_history.append({"role": "user", "content": user_input})
                    if response_text:
                        chat_history.append({"role": "assistant", "content": response_text})
            
            
            else:  # gemini
                # Gemini response handling
                # IMPORTANT: Check for function calls FIRST before accessing .text
                # because .text will throw error if function_call is present
                
                has_function_calls = False
                if hasattr(response, 'candidates') and response.candidates:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            has_function_calls = True
                            break
                
                if has_function_calls:
                    # Handle Gemini function calls
                    print("\n" + "="*60)
                    print("🔧 AI wants to update the following data:")
                    print("="*60)
                    
                    function_calls = []
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            fc = part.function_call
                            
                            # Convert MapComposite to dict recursively
                            def convert_to_dict(obj):
                                if isinstance(obj, dict):
                                    return {k: convert_to_dict(v) for k, v in obj.items()}
                                elif isinstance(obj, list):
                                    return [convert_to_dict(item) for item in obj]
                                elif hasattr(obj, '__dict__'):
                                    return convert_to_dict(dict(obj))
                                else:
                                    return obj
                            
                            args = convert_to_dict(dict(fc.args))
                            
                            readable_name = fc.name.replace('update_', '').replace('_', ' ').title()
                            print(f"\n📝 {readable_name}:")
                            print(json.dumps(args.get('data', args), indent=2))
                            
                            function_calls.append((fc.name, args))
                    
                    print("\n" + "="*60)
                    confirm = input("Apply these updates? (y/n): ").strip().lower()
                    
                    if confirm == 'y':
                        for func_name, args in function_calls:
                            try:
                                if func_name in TOOL_FUNCTIONS:
                                    result = TOOL_FUNCTIONS[func_name](**args)
                                    print(f"✓ {result}")
                            except Exception as e:
                                print(f"✗ Error: {e}")
                        print()
                    else:
                        print("✗ Updates cancelled.\n")
                    
                    chat_history.append({"role": "user", "content": user_input})
                
                elif hasattr(response, 'text') and response.text:
                    # No function calls, just text response
                    print(response.text)
                    chat_history.append({"role": "user", "content": user_input})
                    chat_history.append({"role": "assistant", "content": response.text})
                
                else:
                    print("(No response)")

            
            # Keep last 20 messages
            chat_history = chat_history[-20:]
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()

