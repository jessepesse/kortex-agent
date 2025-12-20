"""LLM provider implementations - All via OpenRouter"""

from openai import OpenAI


# Model mapping for OpenRouter
PROVIDER_MODEL_MAP = {
    "openai": "openai",
    "google": "google", 
    "anthropic": "anthropic",
    "openrouter": None  # Already in correct format
}


class LLMClient:
    """Unified interface - All providers routed through OpenRouter"""
    
    def __init__(self, provider, model, api_key, openrouter_key=None):
        self.provider = provider
        self.model = model
        self.openrouter_key = openrouter_key
        
        # Always use OpenRouter if key is available
        if openrouter_key:
            self.client = OpenAI(
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1"
            )
            self.use_openrouter = True
        elif provider == "openrouter":
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
            self.use_openrouter = True
        else:
            # Fallback to direct API (legacy)
            self.client = OpenAI(api_key=api_key)
            self.use_openrouter = False
    
    def _get_openrouter_model(self):
        """Convert model name to OpenRouter format"""
        if "/" in self.model:
            return self.model
        
        prefix = PROVIDER_MODEL_MAP.get(self.provider, "google")
        if prefix:
            return f"{prefix}/{self.model}"
        return self.model
    
    def chat(self, messages, tools=None):
        """Send chat message with optional tools"""
        if self.use_openrouter:
            return self._chat_openrouter(messages, tools)
        else:
            return self._chat_openai(messages, tools)
    
    def _chat_openrouter(self, messages, tools):
        """OpenRouter chat completion (OpenAI-compatible)"""
        openrouter_model = self._get_openrouter_model()
        
        kwargs = {
            "model": openrouter_model,
            "messages": messages
        }
        
        if tools:
            kwargs["tools"] = tools
        
        response = self.client.chat.completions.create(**kwargs)
        return response
    
    def _chat_openai(self, messages, tools):
        """Fallback OpenAI chat completion"""
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
