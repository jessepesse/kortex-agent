"""
Hive Council - 6 DeepSeek models with specialized personas
Uses OpenRouter API for DeepSeek access
"""

import asyncio
import json
from openai import AsyncOpenAI
import google.generativeai as genai
from ..config import load_config


class HiveService:
    """Hive Council using 6 DeepSeek models with different personas"""
    
    def __init__(self):
        self.config = load_config()
        self.api_keys = self.config.get('api_keys', {})
        
        # Initialize OpenRouter client for DeepSeek
        self.openrouter_client = None
        if self.api_keys.get('openrouter'):
            self.openrouter_client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_keys['openrouter']
            )
        
        # Initialize Gemini for Chairman
        if self.api_keys.get('google'):
            genai.configure(api_key=self.api_keys['google'])
    
    # Define the 6 Hive personas
    PERSONAS = {
        "Devils Advocate": {
            "role": "Challenge every assumption and find logical flaws. Be skeptical and critical.",
            "icon": "⚔️"
        },
        "Pure Data": {
            "role": "You are a pure analytical engine. Only facts, numbers, and patterns matter. No emotions.",
            "icon": "📊"
        },
        "Health Guardian": {
            "role": "Prioritize Jesse's physical and mental health above all. Flag anything that risks burnout or recovery.",
            "icon": "💚"
        },
        "Values Keeper": {
            "role": "Ensure all advice aligns with Jesse's core values and 'truthful' focus. No compromises on principles.",
            "icon": "⚖️"
        },
        "Pragmatic Executor": {
            "role": "Focus on practical execution. Can this be done with Jesse's current energy and schedule? Be realistic.",
            "icon": "🔧"
        },
        "Financial Realist": {
            "role": "Evaluate financial implications and sustainability. Money matters.",
            "icon": "💰"
        }
    }

    async def get_hive_response(self, message, history, context):
        """Query all 6 DeepSeek personas and synthesize with Chairman"""
        
        if not self.openrouter_client:
            return {"error": "OpenRouter API key not configured for Hive Mode"}
        
        # 1. Gather responses from all 6 personas
        tasks = []
        persona_names = list(self.PERSONAS.keys())
        
        for persona_name in persona_names:
            tasks.append(self._query_deepseek_persona(persona_name, message, history, context))
        
        # Run in parallel
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        member_responses = []
        valid_responses = []
        
        for i, result in enumerate(responses):
            persona_name = persona_names[i]
            if isinstance(result, Exception):
                member_responses.append({
                    "model": persona_name,
                    "response": f"Error: {str(result)}",
                    "status": "error"
                })
            else:
                member_responses.append({
                    "model": persona_name,
                    "response": result,
                    "status": "success"
                })
                valid_responses.append({"model": persona_name, "response": result})
        
        # 2. Peer Review Phase (Anonymous)
        peer_reviews = []
        if len(valid_responses) >= 2:
            peer_reviews = await self._get_peer_reviews(valid_responses, persona_names)
        
        # 3. Chairman Synthesis
        chairman_response = await self._synthesize_chairman(message, valid_responses, peer_reviews, context)
        
        return {
            "council_type": "hive",
            "council_responses": member_responses,
            "peer_reviews": peer_reviews,
            "chairman_response": chairman_response
        }
    
    def _build_compact_summary(self, context):
        """Build a compact numerical summary of ALL data"""
        summary = "COMPACT DATA SUMMARY:\n"
        
        # Health metrics
        health = context.get('health', {})
        summary += f"Health: Energy {health.get('current_state', {}).get('energy', '?')}/100, "
        summary += f"Sick leave {health.get('sick_leave', 0)} weeks, "
        summary += f"Status: {health.get('status', 'unknown')}\n"
        
        # Profile
        profile = context.get('profile', {})
        summary += f"Profile: {profile.get('name', '?')}, {profile.get('age', '?')}y, "
        summary += f"Location: {profile.get('current_location', '?')}, "
        summary += f"Focus: {profile.get('focus', '?')}\n"
        
        # Projects
        projects = context.get('active_projects', {})
        project_count = len([v for v in projects.values() if isinstance(v, dict)])
        summary += f"Projects: {project_count} active\n"
        
        # Finance
        finance = context.get('finance', {})
        budget = finance.get('monthly_budget', {})
        summary += f"Finance: Budget {budget.get('total', '?')}€/month\n"
        
        # Routines
        routines = context.get('routines', {})
        routine_count = len([k for k in routines.keys() if isinstance(routines[k], dict)])
        summary += f"Routines: {routine_count} defined\n"
        
        return summary
    
    def _get_persona_context(self, persona_name, context):
        """Get tailored context for each persona (much smaller)"""
        
        if persona_name == "Health Guardian":
            # Only health + relevant routines
            health = context.get('health', {})
            return f"""HEALTH DATA:
Energy: {health.get('current_state', {}).get('energy', '?')}/100
Status: {health.get('status', 'unknown')}
Sick leave: {health.get('sick_leave', 0)} weeks
Diagnoses: {', '.join(health.get('diagnoosi_indikaatio', [])[:3])}
Symptoms: {', '.join(health.get('oireet', [])[:4])}
"""
        
        elif persona_name == "Financial Realist":
            # Only finance + project budgets
            finance = context.get('finance', {})
            budget = finance.get('monthly_budget', {})
            return f"""FINANCE DATA:
Monthly budget: {budget.get('total', '?')}€
Housing: {budget.get('housing', '?')}€
Food: {budget.get('food', '?')}€
Transport: {budget.get('transport', '?')}€
Subscriptions: {json.dumps(finance.get('subscriptions', {}), indent=2)}
"""
        
        elif persona_name == "Values Keeper":
            # Only values + profile focus/guide
            values = context.get('values', {})
            profile = context.get('profile', {})
            core_values = values.get('core_values', [])
            anti_values = values.get('anti_values', [])
            core_str = ', '.join(core_values[:5]) if isinstance(core_values, list) else str(core_values)
            anti_str = ', '.join(anti_values[:5]) if isinstance(anti_values, list) else str(anti_values)
            return f"""VALUES & PRINCIPLES:
Core values: {core_str}
Anti-values: {anti_str}
Current focus: {profile.get('focus', 'unknown')}
Guide: {profile.get('guide', 'none')}
"""
        
        elif persona_name == "Pragmatic Executor":
            # Only projects + routines
            projects = context.get('active_projects', {})
            routines = context.get('routines', {})
            return f"""EXECUTION DATA:
Active projects: {json.dumps(projects, indent=2)[:500]}...
Weekly routines: {json.dumps(routines, indent=2)[:500]}...
"""
        
        elif persona_name in ["Pure Data", "Devils Advocate"]:
            # Both get compact summary of everything
            return self._build_compact_summary(context)
        
        return "No specific context"
    
    def _build_persona_prompt(self, persona_name, context):
        """Build system prompt for a specific persona (with tailored context)"""
        persona = self.PERSONAS[persona_name]
        
        # Get tailored context for this persona
        persona_context = self._get_persona_context(persona_name, context)
        
        prompt = f"""You are '{persona_name}' in Jesse's Hive Council.

YOUR ROLE: {persona['role']}

{persona_context}

Stay true to your role as '{persona_name}'. Provide a focused, actionable perspective based on YOUR domain."""
        return prompt
    
    async def _query_deepseek_persona(self, persona_name, message, history, context):
        """Query a single DeepSeek persona"""
        print(f"✨ Querying {persona_name}...")
        try:
            system_prompt = self._build_persona_prompt(persona_name, context)
            
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add simplified history
            for msg in history[-5:]:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
            
            messages.append({"role": "user", "content": message})
            
            # Retry logic for unstable providers
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    response = await self.openrouter_client.chat.completions.create(
                        model="deepseek/deepseek-v3.2-speciale",
                        messages=messages,
                        extra_body={"reasoning": {"enabled": True}}
                    )
                    print(f"✅ {persona_name} responded")
                    return response.choices[0].message.content
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"⚠️ {persona_name} attempt {attempt + 1} failed, retrying...")
                        await asyncio.sleep(1)  # Wait before retry
                    else:
                        print(f"❌ {persona_name} failed after {max_retries} attempts: {e}")
                        raise e
            
        except Exception as e:
            print(f"❌ {persona_name} failed: {e}")
            raise e
    
    async def _get_peer_reviews(self, valid_responses, persona_names):
        """Anonymous peer review phase"""
        import random
        
        print("🔍 Starting anonymous peer review...")
        
        # Anonymize responses
        anonymized = []
        response_map = {}
        
        for idx, resp in enumerate(valid_responses):
            label = chr(65 + idx)  # A, B, C...
            anonymized.append({"label": f"Response {label}", "text": resp["response"]})
            response_map[label] = resp["model"]
        
        random.shuffle(anonymized)
        anon_text = "\n\n".join([f"**{item['label']}:**\n{item['text']}" for item in anonymized])
        
        # Each persona reviews (pick 3 random reviewers to save cost)
        review_tasks = []
        reviewers = random.sample(persona_names, min(3, len(persona_names)))
        
        for reviewer in reviewers:
            review_tasks.append(self._get_deepseek_review(reviewer, anon_text))
        
        reviews = await asyncio.gather(*review_tasks, return_exceptions=True)
        
        # Format reviews
        peer_reviews = []
        for idx, review in enumerate(reviews):
            if not isinstance(review, Exception) and review:
                peer_reviews.append({
                    "reviewer": f"Member {chr(65 + idx)}",  # Anonymous
                    "review": review
                })
        
        print(f"✅ Collected {len(peer_reviews)} peer reviews")
        return peer_reviews
    
    async def _get_deepseek_review(self, persona_name, anonymized_responses):
        """Get peer review from a persona"""
        try:
            prompt = f"""You are a peer reviewer in an anonymous council process.

Review the following responses critically and objectively:

{anonymized_responses}

Provide a brief critique:
1. Strengths and weaknesses of each response
2. Which response(s) have the most actionable advice
3. Any blind spots or biases

Be concise (2-3 sentences per response). Do not reveal your identity."""
            
            response = await self.openrouter_client.chat.completions.create(
                model="deepseek/deepseek-v3.2",
                messages=[{"role": "user", "content": prompt}],
                extra_body={"reasoning": {"enabled": True}}
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ Review failed: {e}")
            return None
    
    async def _synthesize_chairman(self, message, valid_responses, peer_reviews, context):
        """Chairman synthesizes Hive responses"""
        if not valid_responses:
            return "Hive failed to reach quorum. No valid responses received."
        
        # Get chairman model from config (default: gemini-3-pro-preview)
        chairman_model = self.config.get('chairman_model', 'gemini-3-pro-preview')
        model = genai.GenerativeModel(chairman_model)
        
        # Format responses
        responses_text = "\n\n".join([
            f"### {resp['model']}\n{resp['response']}" 
            for resp in valid_responses
        ])
        
        # Format peer reviews
        reviews_text = ""
        if peer_reviews:
            reviews_text = "\n\nPEER REVIEWS (Anonymous):\n" + "\n\n".join([
                f"**{pr['reviewer']}:**\n{pr['review']}" 
                for pr in peer_reviews
            ])
        
        prompt = f"""You are the Chairman synthesizing the Hive Council's responses.

The Hive is a collective of 6 specialized DeepSeek personas, each bringing a unique perspective.

USER QUERY: {message}

HIVE PERSPECTIVES:
{responses_text}
{reviews_text}

YOUR TASK:
1. Identify consensus and conflicts between personas
2. Consider the peer reviews - they reveal blind spots and strengths
3. Synthesize into a concrete, unified action plan
4. Be direct and pragmatic
5. Make a final decision

Format your response in Markdown.
"""
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: model.generate_content(prompt)
            )
            return response.text
        except Exception as e:
            return f"**Chairman Error:** Failed to synthesize. Error: {str(e)}"
