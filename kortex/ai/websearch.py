"""Web Search Pipeline - Scout -> Specialist -> Synthesizer"""

import asyncio
from openai import AsyncOpenAI
from ..config import load_config
from .scout import get_scout_service


class WebSearchService:
    """
    Scout-powered web search pipeline:
    1. Scout (Flash-Lite) - analyzes if search needed, recommends model
    2. Specialist (Grok or Perplexity) - fetches web data
    3. Synthesizer (user's model) - generates final response
    
    Search models:
    - NEWS: x-ai/grok-4.1-fast:online (fast, X + web)
    - RESEARCH: perplexity/sonar-pro-search (deep, authoritative)
    - FORCE: Always Grok (budget protection)
    """
    
    GROK_MODEL = "x-ai/grok-4.1-fast:online"
    PERPLEXITY_MODEL = "perplexity/sonar-pro-search"
    
    def __init__(self):
        self.config = load_config()
        self.api_keys = self.config.get('api_keys', {})
        self.scout = get_scout_service()
        
        # OpenRouter client for all LLM calls
        self.openrouter_client = None
        if self.api_keys.get('openrouter'):
            self.openrouter_client = AsyncOpenAI(
                api_key=self.api_keys['openrouter'],
                base_url="https://openrouter.ai/api/v1"
            )
    
    async def search_with_scout(self, message, history, context, user_model, user_provider, 
                                 reasoning_enabled=False, force_model=None):
        """
        Main pipeline entry point with Scout integration.
        
        Args:
            message: User's question
            history: Chat history
            context: User context data
            user_model: User's selected chat model
            user_provider: User's selected provider
            reasoning_enabled: Whether reasoning is enabled for user's model
            force_model: Override Scout's recommendation (None, 'grok', 'perplexity')
            
        Returns:
            dict with response, search_type, sources, scout_info, etc.
        """
        print("🔍 Web Search Pipeline (Scout-powered) starting...")
        
        # Stage 1: Scout analysis
        scout_result = await self.scout.analyze(message, history)
        print(f"🕵️ Scout: {scout_result['decision']} ({scout_result['confidence']}%) - {scout_result['search_type']}")
        
        # Determine which model to use
        if force_model:
            # User explicitly chose a model
            if force_model == 'grok':
                search_model = self.GROK_MODEL
            else:
                search_model = self.PERPLEXITY_MODEL
            scout_result['used_model'] = search_model
            scout_result['override_reason'] = f"User selected {force_model}"
        elif scout_result['decision'] == 'FORCE_SEARCH':
            # FORCE always uses Grok (budget protection)
            search_model = self.GROK_MODEL
            scout_result['used_model'] = search_model
            if scout_result['search_type'] == 'RESEARCH':
                scout_result['override_reason'] = "FORCE always uses Grok (budget protection)"
        else:
            # Use Scout's recommendation
            search_model = scout_result['recommended_model']
            scout_result['used_model'] = search_model
        
        search_type = scout_result['search_type']
        print(f"📍 Using: {search_model} (Scout recommended: {scout_result['recommended_model']})")
        
        # Stage 2: Specialist search
        search_result = await self._specialist_search(message, search_model)
        print(f"📥 Specialist returned {len(search_result.get('content', ''))} chars")
        
        # Stage 3: Synthesizer - user's model with context
        final_response = await self._synthesize_response(
            message, 
            search_result, 
            search_type,
            history,
            context,
            user_model,
            user_provider,
            reasoning_enabled
        )
        
        return {
            "response": final_response,
            "search_type": search_type,
            "sources": search_result.get("sources", []),
            "specialist_model": search_result.get("model", ""),
            "raw_search_data": search_result.get("content", ""),
            "scout": {
                "decision": scout_result['decision'],
                "confidence": scout_result['confidence'],
                "search_type": scout_result['search_type'],
                "reason": scout_result['reason'],
                "recommended_model": scout_result['recommended_model'],
                "used_model": scout_result['used_model'],
                "override_reason": scout_result.get('override_reason')
            }
        }
    
    async def _specialist_search(self, message, model):
        """
        Stage 2: Specialist - fetches web data using specified model.
        """
        if not self.openrouter_client:
            return {
                "content": "Web search unavailable - OpenRouter API key missing",
                "sources": [],
                "model": "none"
            }
        
        try:
            if 'grok' in model.lower():
                return await self._grok_search(message)
            else:
                return await self._perplexity_search(message)
        except Exception as e:
            print(f"❌ Specialist search failed: {e}")
            return {
                "content": f"Search failed: {str(e)}",
                "sources": [],
                "model": "error"
            }
    
    async def _grok_search(self, message):
        """
        Search using Grok-4.1-fast with native X + web search.
        """
        print("🐦 Grok-4.1-fast: Searching X and web...")
        
        response = await self.openrouter_client.chat.completions.create(
            model=self.GROK_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You are a research assistant with access to X (Twitter) and web search.
Find the most relevant and up-to-date information.
Return structured findings:
- Key facts discovered
- Sources/links found
- Timestamps if available
Be thorough but concise."""
                },
                {
                    "role": "user", 
                    "content": message
                }
            ]
        )
        
        content = response.choices[0].message.content
        sources = self._extract_sources(response.choices[0].message)
        
        return {
            "content": content,
            "sources": sources,
            "model": self.GROK_MODEL
        }
    
    async def _perplexity_search(self, message):
        """
        Search using Perplexity Sonar Pro with reasoning.
        """
        print("🔬 Perplexity Sonar Pro: Deep research with reasoning...")
        
        response = await self.openrouter_client.chat.completions.create(
            model=self.PERPLEXITY_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You are a research assistant conducting deep web research.
Search for authoritative sources and compile comprehensive findings.
Return structured research data:
- Key findings with sources
- Technical details if applicable
- Relevant statistics or data points
Focus on accuracy and cite your sources."""
                },
                {
                    "role": "user",
                    "content": message
                }
            ],
            extra_body={"reasoning": {"enabled": True}}
        )
        
        content = response.choices[0].message.content
        sources = self._extract_sources(response.choices[0].message)
        
        return {
            "content": content,
            "sources": sources,
            "model": self.PERPLEXITY_MODEL
        }
    
    def _extract_sources(self, message):
        """Extract sources from message annotations/citations."""
        sources = []
        
        # Check for citations (Perplexity style)
        if hasattr(message, 'citations') and message.citations:
            for citation in message.citations:
                if isinstance(citation, str):
                    sources.append({"url": citation, "title": ""})
                elif hasattr(citation, 'url'):
                    sources.append({
                        "url": citation.url,
                        "title": getattr(citation, 'title', ''),
                    })
        
        # Check for annotations (OpenRouter standardized)
        if hasattr(message, 'annotations') and message.annotations:
            for ann in message.annotations:
                if hasattr(ann, 'type') and ann.type == "url_citation":
                    sources.append({
                        "url": ann.url_citation.url,
                        "title": getattr(ann.url_citation, 'title', ''),
                    })
        
        return sources
    
    async def _synthesize_response(self, original_message, search_result, search_type, 
                                    history, context, user_model, user_provider, reasoning_enabled):
        """
        Stage 3: Synthesizer - User's model generates final response with search context.
        """
        print(f"✨ Synthesizer ({user_provider}/{user_model}): Generating response...")
        
        # Build enhanced message with search results
        search_context = f"""I found the following information from web search:

## Web Search Results ({search_type})
**Search performed by:** {search_result.get('model', 'Unknown')}

### Findings:
{search_result.get('content', 'No results')}

### Sources:
{self._format_sources(search_result.get('sources', []))}

---

Based on the above search results, please answer my original question:

{original_message}

Please cite sources when relevant using markdown links."""
        
        # Use the handler's existing infrastructure
        from .handler import get_ai_response
        
        # Prepare reasoning config if enabled
        reasoning_config = {"enabled": True} if reasoning_enabled else None
        
        # Get response from user's selected model
        response = get_ai_response(
            message=search_context,
            history=history,
            model=user_model,
            provider=user_provider,
            api_key=self.api_keys.get(user_provider, self.api_keys.get('openrouter', '')),
            files=None,
            openrouter_reasoning_config=reasoning_config
        )
        
        # get_ai_response returns a dict with 'response' key
        if isinstance(response, dict):
            return response.get('response', str(response))
        return response
    
    def _format_sources(self, sources):
        """Format sources as markdown links"""
        if not sources:
            return "No sources available"
        
        formatted = []
        for src in sources:
            title = src.get('title', src.get('url', 'Unknown'))
            url = src.get('url', '#')
            formatted.append(f"- [{title}]({url})")
        
        return "\n".join(formatted)


# Singleton instance
_websearch_service = None

def get_websearch_service():
    global _websearch_service
    if _websearch_service is None:
        _websearch_service = WebSearchService()
    return _websearch_service


async def web_search_response(message, history, context, user_model, user_provider, 
                               reasoning_enabled=False, force_model=None):
    """
    Convenience function for web search pipeline.
    
    Args:
        force_model: Override Scout's recommendation ('grok' or 'perplexity')
    """
    service = get_websearch_service()
    return await service.search_with_scout(
        message=message,
        history=history,
        context=context,
        user_model=user_model,
        user_provider=user_provider,
        reasoning_enabled=reasoning_enabled,
        force_model=force_model
    )


async def scout_only(message, history=None):
    """
    Run Scout analysis only, without performing search.
    Used for checking if search is needed before user confirms.
    """
    scout = get_scout_service()
    return await scout.analyze(message, history)
