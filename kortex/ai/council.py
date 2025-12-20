import asyncio
import json
import os
from openai import AsyncOpenAI
from ..config import load_config

class CouncilService:
    def __init__(self):
        self.config = load_config()
        self.api_keys = self.config.get('api_keys', {})
        
        # All models use OpenRouter
        self.openrouter_client = None
        if self.api_keys.get('openrouter'):
            self.openrouter_client = AsyncOpenAI(
                api_key=self.api_keys['openrouter'],
                base_url="https://openrouter.ai/api/v1"
            )

    async def get_council_response(self, message, history, context):
        """
        Query council members in parallel and synthesize a response.
        """
        if not self.openrouter_client:
            return {"error": "No OpenRouter API key configured for Council Mode"}
        
        # 1. Gather responses from all members
        tasks = []
        members = []

        # Gemini Member (via OpenRouter)
        tasks.append(self._query_gemini(message, history, context))
        members.append("Gemini 3 Pro Preview")

        # GPT-5.2 Member (via OpenRouter)
        tasks.append(self._query_gpt52(message, history, context))
        members.append("GPT-5.2")

        # Claude Member (via OpenRouter)
        tasks.append(self._query_claude(message, history, context))
        members.append("Claude Haiku 4.5")

        if not tasks:
            return {"error": "No AI providers configured for Council Mode"}

        # Run in parallel
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        member_responses = []
        valid_responses = []
        
        for i, result in enumerate(responses):
            member_name = members[i]
            if isinstance(result, Exception):
                member_responses.append({
                    "model": member_name,
                    "response": f"Error: {str(result)}",
                    "status": "error"
                })
            else:
                member_responses.append({
                    "model": member_name,
                    "response": result,
                    "status": "success"
                })
                valid_responses.append({"model": member_name, "response": result})

        # 2. Peer Review Phase (Anonymous)
        peer_reviews = []
        if len(valid_responses) >= 2:
            peer_reviews = await self._get_peer_reviews(valid_responses, members, tasks)

        # 3. Chairman Synthesis
        chairman_response = await self._synthesize_chairman(message, valid_responses, peer_reviews, context)

        return {
            "council_responses": member_responses,
            "peer_reviews": peer_reviews,
            "chairman_response": chairman_response
        }

    def _build_system_prompt(self, context):
        prompt = """You are a neutral, objective, and analytical advisor in Jesse Saarinen's Kortex Council.
Your goal is to provide a distinct perspective based on the user's life data.

CONTEXT:
"""
        for key, data in context.items():
            prompt += f"\n## {key.upper().replace('_', ' ')}\n"
            prompt += f"```json\n{json.dumps(data, indent=2)}\n```\n"
            
        prompt += "\nProvide a concise, actionable analysis based on this data. Be direct."
        return prompt

    async def _query_gemini(self, message, history, context):
        print("✨ Querying Gemini via OpenRouter...")
        try:
            system_prompt = self._build_system_prompt(context)
            messages = [{"role": "system", "content": system_prompt}]
            messages.append({"role": "user", "content": message})
            
            response = await self.openrouter_client.chat.completions.create(
                model="google/gemini-3-pro-preview",
                messages=messages
            )
            
            print("✅ Gemini responded")
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ Gemini failed: {e}")
            return f"Gemini encountered an error: {str(e)}"

    async def _query_gpt52(self, message, history, context):
        print("✨ Querying GPT-5.2 via OpenRouter...")
        try:
            system_prompt = self._build_system_prompt(context)
            messages = [{"role": "system", "content": system_prompt}]
            # Add simplified history (last 5 messages)
            for msg in history[-5:]:
                messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
            messages.append({"role": "user", "content": message})

            response = await self.openrouter_client.chat.completions.create(
                model="openai/gpt-5.2",
                messages=messages,
                extra_body={"reasoning": {"enabled": True}}
            )
            print("✅ GPT-5.2 responded")
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ GPT-5.2 failed: {e}")
            raise e

    async def _query_claude(self, message, history, context):
        print("✨ Querying Claude via OpenRouter...")
        try:
            system_prompt = self._build_system_prompt(context)
            messages = [{"role": "system", "content": system_prompt}]
            for msg in history[-5:]:
                role = msg.get("role", "user")
                if role not in ['user', 'assistant']:
                    role = 'user' 
                messages.append({"role": role, "content": msg.get("content", "")})
            messages.append({"role": "user", "content": message})

            response = await self.openrouter_client.chat.completions.create(
                model="anthropic/claude-haiku-4-5",
                messages=messages
            )
            print("✅ Claude responded")
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ Claude failed: {e}")
            raise e

    async def _get_peer_reviews(self, valid_responses, members, original_tasks):
        """
        Each member reviews OTHER members' responses anonymously.
        Shuffle responses to maintain anonymity.
        """
        import random
        
        print("🔍 Starting peer review phase...")
        
        # Create anonymized response list (shuffle and label as Response A, B, C)
        anonymized = []
        response_map = {}  # Maps anonymous label to actual model
        
        for idx, resp in enumerate(valid_responses):
            label = chr(65 + idx)  # A, B, C...
            anonymized.append({"label": f"Response {label}", "text": resp["response"]})
            response_map[label] = resp["model"]
        
        # Shuffle to prevent pattern recognition
        random.shuffle(anonymized)
        
        # Build the anonymized responses text
        anon_text = "\n\n".join([f"**{item['label']}:**\n{item['text']}" for item in anonymized])
        
        # Each member reviews the anonymized responses (all via OpenRouter)
        review_tasks = []
        
        # Gemini review
        if any(r["model"] == "Gemini 3 Pro Preview" for r in valid_responses):
            review_tasks.append(self._get_gemini_review(anon_text))
        
        # GPT-5.2 review
        if any(r["model"] == "GPT-5.2" for r in valid_responses):
            review_tasks.append(self._get_gpt52_review(anon_text))
        
        # Claude review
        if any(r["model"] == "Claude Haiku 4.5" for r in valid_responses):
            review_tasks.append(self._get_claude_review(anon_text))
        
        reviews = await asyncio.gather(*review_tasks, return_exceptions=True)
        
        # Format reviews anonymously
        peer_reviews = []
        reviewer_labels = ["Member A", "Member B", "Member C"]
        
        for idx, review in enumerate(reviews):
            if not isinstance(review, Exception) and review:
                peer_reviews.append({
                    "reviewer": reviewer_labels[idx] if idx < len(reviewer_labels) else f"Member {idx+1}",
                    "review": review
                })
        
        print(f"✅ Collected {len(peer_reviews)} peer reviews")
        return peer_reviews

    async def _get_gemini_review(self, anonymized_responses):
        """Gemini reviews anonymized responses via OpenRouter"""
        try:
            prompt = f"""You are a peer reviewer in an anonymous council process.
Review the following responses critically and objectively:

{anonymized_responses}

Provide a brief critique identifying:
1. Strengths and weaknesses of each response
2. Which response(s) have the most actionable advice
3. Any blind spots or biases you notice

Be concise (2-3 sentences per response). Do not reveal your identity."""
            
            response = await self.openrouter_client.chat.completions.create(
                model="google/gemini-3-pro-preview",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ Gemini review failed: {e}")
            return None

    async def _get_gpt52_review(self, anonymized_responses):
        """GPT-5.2 reviews anonymized responses via OpenRouter"""
        try:
            response = await self.openrouter_client.chat.completions.create(
                model="openai/gpt-5.2",
                messages=[{
                    "role": "user",
                    "content": f"""You are a peer reviewer in an anonymous council process.
Review the following responses critically and objectively:

{anonymized_responses}

Provide a brief critique identifying:
1. Strengths and weaknesses of each response
2. Which response(s) have the most actionable advice
3. Any blind spots or biases you notice

Be concise (2-3 sentences per response). Do not reveal your identity."""
                }],
                extra_body={"reasoning": {"enabled": True}}
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ OpenAI review failed: {e}")
            return None

    async def _get_claude_review(self, anonymized_responses):
        """Claude reviews anonymized responses via OpenRouter"""
        try:
            response = await self.openrouter_client.chat.completions.create(
                model="anthropic/claude-haiku-4-5",
                messages=[{
                    "role": "user",
                    "content": f"""You are a peer reviewer in an anonymous council process.
Review the following responses critically and objectively:

{anonymized_responses}

Provide a brief critique identifying:
1. Strengths and weaknesses of each response
2. Which response(s) have the most actionable advice
3. Any blind spots or biases you notice

Be concise (2-3 sentences per response). Do not reveal your identity."""
                }]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ Claude review failed: {e}")
            return None

    async def _synthesize_chairman(self, message, valid_responses, peer_reviews, context):
        if not valid_responses:
            return "Council failed to reach a quorum. No valid responses received."

        # Format responses
        responses_text = "\n\n".join([f"### {resp['model']}\n{resp['response']}" for resp in valid_responses])
        
        # Format peer reviews
        reviews_text = ""
        if peer_reviews:
            reviews_text = "\n\nPEER REVIEWS (Anonymous):\n" + "\n\n".join([
                f"**{pr['reviewer']}:**\n{pr['review']}" for pr in peer_reviews
            ])
        
        prompt = f"""You are the Chairman of Jesse's Kortex Council.
Your role is to review the opinions of the council members AND their peer reviews, then make a final, binding decision.

USER QUERY: {message}

COUNCIL OPINIONS:
{responses_text}
{reviews_text}

YOUR TASK:
1. Identify consensus and conflicts between members.
2. Consider the peer reviews - they highlight blind spots and strengths.
3. Synthesize the best advice into a concrete action plan.
4. Be direct, pragmatic, and "no-bullshit".
5. Make a final decision.

Format your response in Markdown.
"""
        
        # Use OpenRouter for Chairman (Gemini 3 Pro)
        try:
            response = await self.openrouter_client.chat.completions.create(
                model="google/gemini-3-pro-preview",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"**Chairman Error:** Failed to synthesize response. Error: {str(e)}"
