"""LLM provider implementations"""

import google.generativeai as genai
from openai import OpenAI


class LLMClient:
    """Unified interface for OpenAI and Gemini"""
    
    def __init__(self, provider, model, api_key):
        self.provider = provider
        self.model = model
        
        if provider == "openai":
            self.client = OpenAI(api_key=api_key)
        elif provider == "google":
            genai.configure(api_key=api_key)
            self.client = None  # Gemini uses global config
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def chat(self, messages, tools=None):
        """Send chat message with optional tools"""
        if self.provider == "openai":
            return self._chat_openai(messages, tools)
        else:
            return self._chat_gemini(messages, tools)
    
    def _chat_openai(self, messages, tools):
        """OpenAI chat completion"""
        # Convert tools to OpenAI format
        openai_tools = []
        if tools:
            for tool_func in tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool_func.__name__,
                        "description": tool_func.__doc__ or "",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "data": {"type": "object"}
                            }
                        }
                    }
                })
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=openai_tools if openai_tools else None
        )
        
        return response
    
    def _chat_gemini(self, messages, tools):
        """Gemini chat completion"""
        # Convert messages to Gemini format
        # For simplicity, use the existing Gemini approach
        model = genai.GenerativeModel(
            model_name=self.model,
            tools=list(tools) if tools else None
        )
        
        # Extract last user message
        user_message = messages[-1]["content"] if messages else ""
        
        response = model.generate_content(user_message)
        return response
