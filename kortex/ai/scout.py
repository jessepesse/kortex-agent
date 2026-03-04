"""Scout Service - Intelligent search decision maker"""

import json
from openai import AsyncOpenAI
from ..config import load_config


class ScoutService:
    """
    Scout analyzes user messages and decides:
    - NO_SEARCH (0-60%): No web search needed
    - SUGGEST_SEARCH (61-99%): Suggest search, user decides
    - FORCE_SEARCH (100%): Auto-search with Grok (live data)
    
    Also recommends search_type: NEWS (Grok) or RESEARCH (Perplexity)
    """
    
    SCOUT_MODEL = "google/gemini-3.1-flash-lite-preview"
    
    SCOUT_PROMPT = """You are Scout, an intelligent classifier that decides if a user question needs fresh web data.

Analyze the question and return a JSON response:

{
  "decision": "NO_SEARCH" | "SUGGEST_SEARCH" | "FORCE_SEARCH",
  "confidence": 0-100,
  "search_type": "NEWS" | "RESEARCH",
  "reason": "Brief explanation in same language as the question"
}

DECISION RULES:

FORCE_SEARCH (confidence: 100) - ONLY for real-time data:
- Current prices (stocks, crypto, currencies) - "What's Bitcoin price NOW"
- Live weather - "Weather in Helsinki right now"
- Live sports scores - "Current score of the match"
- Breaking news happening today - "What just happened in X"

SUGGEST_SEARCH (confidence: 61-99) - Fresh data would help:
- Recent software updates/releases - "What's new in CachyOS update"
- Recent events (last weeks/months)
- Technical docs that change often
- Comparisons that need current info
- News/trends from recent past

NO_SEARCH (confidence: 0-60) - No web search needed:
- Philosophy, opinions, advice
- Historical facts
- Personal questions (user's own data)
- Programming concepts (unless about newest versions)
- Math, science fundamentals
- Creative writing

SEARCH_TYPE RULES:

NEWS - Use Grok (fast, X/Twitter + web):
- Breaking news, current events
- Social media trends, viral content
- Stock/crypto prices
- Sports scores, weather
- Celebrity news, rumors

RESEARCH - Use Perplexity (deep, authoritative sources):
- Technical documentation
- Scientific research
- Product comparisons/reviews
- How-to guides needing current info
- Academic topics
- Software/API documentation

Respond ONLY with valid JSON, no markdown or extra text."""

    def __init__(self):
        self.config = load_config()
        self.api_keys = self.config.get('api_keys', {})
        
        self.client = None
        if self.api_keys.get('openrouter'):
            self.client = AsyncOpenAI(
                api_key=self.api_keys['openrouter'],
                base_url="https://openrouter.ai/api/v1"
            )
    
    async def analyze(self, message: str, history: list = None) -> dict:
        """
        Analyze a message and return search decision.
        
        Returns:
            {
                "decision": "NO_SEARCH" | "SUGGEST_SEARCH" | "FORCE_SEARCH",
                "confidence": int (0-100),
                "search_type": "NEWS" | "RESEARCH",
                "reason": str,
                "recommended_model": str,  # What Scout recommends
                "used_model": str | None,  # What will actually be used (for FORCE)
                "override_reason": str | None  # Why override (for FORCE)
            }
        """
        if not self.client:
            return self._default_response("No OpenRouter API key")
        
        try:
            # Build context from recent history if available
            context = ""
            if history and len(history) > 0:
                recent = history[-3:]  # Last 3 messages for context
                context = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')[:200]}" for m in recent])
                context = f"\nRecent conversation:\n{context}\n\n"
            
            prompt = f"{context}User question: {message}"
            
            response = await self.client.chat.completions.create(
                model=self.SCOUT_MODEL,
                messages=[
                    {"role": "system", "content": self.SCOUT_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.1  # Low temp for consistent classification
            )
            
            result_text = response.choices[0].message.content
            
            # Handle None or empty response
            if not result_text:
                print("❌ Scout received empty response from LLM")
                return self._default_response("Empty LLM response")
            
            result_text = result_text.strip()
            print(f"🔍 Scout raw response: {result_text[:200]}...")
            
            # Parse JSON response
            # Handle potential markdown code blocks
            if result_text.startswith("```"):
                parts = result_text.split("```")
                if len(parts) >= 2:
                    result_text = parts[1]
                    if result_text.startswith("json"):
                        result_text = result_text[4:]
                    result_text = result_text.strip()
            
            # Try to extract JSON if mixed with other text
            if not result_text.startswith("{"):
                import re
                json_match = re.search(r'\{[^{}]*\}', result_text, re.DOTALL)
                if json_match:
                    result_text = json_match.group()
            
            result = json.loads(result_text)
            
            # Validate and normalize - handle None values explicitly
            decision = (result.get("decision") or "NO_SEARCH").upper()
            if decision not in ["NO_SEARCH", "SUGGEST_SEARCH", "FORCE_SEARCH"]:
                decision = "NO_SEARCH"
            
            confidence = int(result.get("confidence") or 50)
            confidence = max(0, min(100, confidence))
            
            search_type = (result.get("search_type") or "RESEARCH").upper()
            if search_type not in ["NEWS", "RESEARCH"]:
                search_type = "RESEARCH"
            
            reason = result.get("reason") or ""
            
            # Determine recommended model based on search_type
            if search_type == "NEWS":
                recommended_model = "x-ai/grok-4.1-fast:online"
            else:
                recommended_model = "perplexity/sonar-pro-search"
            
            response_data = {
                "decision": decision,
                "confidence": confidence,
                "search_type": search_type,
                "reason": reason,
                "recommended_model": recommended_model,
                "used_model": None,
                "override_reason": None
            }
            
            # For FORCE_SEARCH, always use Grok (budget protection)
            if decision == "FORCE_SEARCH":
                response_data["used_model"] = "x-ai/grok-4.1-fast:online"
                if search_type == "RESEARCH":
                    response_data["override_reason"] = "FORCE always uses Grok (budget protection)"
            
            print(f"🕵️ Scout: {decision} ({confidence}%) - {search_type} - {reason[:50]}...")
            
            return response_data
            
        except json.JSONDecodeError as e:
            print(f"❌ Scout JSON parse error: {e}")
            return self._default_response(f"JSON parse error: {str(e)}")
        except Exception as e:
            print(f"❌ Scout error: {e}")
            return self._default_response(str(e))
    
    def _default_response(self, error: str) -> dict:
        """Return safe default when Scout fails."""
        return {
            "decision": "SUGGEST_SEARCH",
            "confidence": 70,
            "search_type": "RESEARCH",
            "reason": f"Scout unavailable: {error}",
            "recommended_model": "x-ai/grok-4.1-fast:online",
            "used_model": None,
            "override_reason": None
        }


# Singleton instance
_scout_service = None

def get_scout_service():
    global _scout_service
    if _scout_service is None:
        _scout_service = ScoutService()
    return _scout_service

async def scout_analyze(message: str, history: list = None) -> dict:
    """Convenience function for Scout analysis."""
    service = get_scout_service()
    return await service.analyze(message, history)
