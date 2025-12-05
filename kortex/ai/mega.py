"""
Mega Council - Ultimate decision system combining Elite and Hive
"""

import asyncio
import json
import google.generativeai as genai
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from .council import CouncilService
from .hive import HiveService
from ..config import load_config


class MegaCouncilService:
    """Mega Council: Elite + Hive battle → Ultimate Chairman verdict"""
    
    def __init__(self):
        self.config = load_config()
        self.elite_service = CouncilService()
        self.hive_service = HiveService()
    
    async def get_mega_response(self, message, history, context):
        """Run both Elite and Hive, then synthesize with Mega Chairman"""
        
        print("🔥 MEGA COUNCIL ACTIVATED")
        
        # Run Elite and Hive in parallel
        elite_task = self._run_elite_with_voting(message, history, context)
        hive_task = self._run_hive_with_voting(message, history, context)
        
        elite_result, hive_result = await asyncio.gather(elite_task, hive_task)
        
        # Mega Chairman synthesis
        mega_verdict = await self._mega_chairman_synthesis(
            message, 
            elite_result, 
            hive_result, 
            context
        )
        
        return {
            "council_type": "mega",
            "elite_winner": elite_result,
            "hive_winner": hive_result,
            "mega_verdict": mega_verdict
        }
    
    async def _run_elite_with_voting(self, message, history, context):
        """Elite Council with peer review voting"""
        print("🏛️ Elite Council: Starting deliberation...")
        
        # Get all Elite responses
        elite_full = await self.elite_service.get_council_response(message, history, context)
        
        responses = elite_full.get('council_responses', [])
        if not responses:
            return {"winner": "No Elite responses", "votes": {}}
        
        # Peer review voting
        print("🏛️ Elite: Peer review voting...")
        votes = await self._elite_voting(responses, message)
        
        # Find winner
        winner_model = max(votes, key=votes.get)
        winner_response = next((r for r in responses if r['model'] == winner_model), None)
        
        # Winner refines answer
        if winner_response:
            refined = await self._refine_answer(winner_model, winner_response['response'], message, context, "elite")
            winner_response['response'] = refined
        
        print(f"🏆 Elite Winner: {winner_model} ({votes[winner_model]} votes)")
        
        return {
            "winner_model": winner_model,
            "winner_response": winner_response.get('response', '') if winner_response else '',
            "votes": votes,
            "all_responses": responses
        }
    
    async def _run_hive_with_voting(self, message, history, context):
        """Hive Council with persona voting"""
        print("🐝 Hive Council: Starting deliberation...")
        
        # Get all Hive responses
        hive_full = await self.hive_service.get_hive_response(message, history, context)
        
        responses = hive_full.get('council_responses', [])
        if not responses:
            return {"winner": "No Hive responses", "votes": {}}
        
        # Persona voting
        print("🐝 Hive: Persona voting...")
        votes = await self._hive_voting(responses, message)
        
        # Find winner
        winner_persona = max(votes, key=votes.get)
        winner_response = next((r for r in responses if r['model'] == winner_persona), None)
        
        # Winner refines answer
        if winner_response:
            refined = await self._refine_answer(winner_persona, winner_response['response'], message, context, "hive")
            winner_response['response'] = refined
        
        print(f"🏆 Hive Winner: {winner_persona} ({votes[winner_persona]} votes)")
        
        return {
            "winner_model": winner_persona,
            "winner_response": winner_response.get('response', '') if winner_response else '',
            "votes": votes,
            "all_responses": responses
        }
    
    async def _elite_voting(self, responses, message):
        """Each Elite model votes for best response (peer review style)"""
        votes = {r['model']: 0 for r in responses if r['status'] == 'success'}
        
        # Anonymize responses
        import random
        anonymized = [(chr(65 + i), r['response']) for i, r in enumerate(responses) if r['status'] == 'success']
        random.shuffle(anonymized)
        
        anon_text = "\n\n".join([f"**Response {label}:**\n{text}" for label, text in anonymized])
        
        # Each model votes
        voting_tasks = []
        for response in responses:
            if response['status'] == 'success':
                voting_tasks.append(self._get_elite_vote(response['model'], anon_text, message))
        
        vote_results = await asyncio.gather(*voting_tasks, return_exceptions=True)
        
        # Count votes
        label_to_model = {chr(65 + i): r['model'] for i, r in enumerate(responses) if r['status'] == 'success'}
        
        for vote in vote_results:
            if isinstance(vote, str) and vote in label_to_model:
                votes[label_to_model[vote]] += 1
        
        return votes
    
    async def _hive_voting(self, responses, message):
        """Each Hive persona votes for best response"""
        votes = {r['model']: 0 for r in responses if r['status'] == 'success'}
        
        # Anonymize
        import random
        anonymized = [(chr(65 + i), r['response']) for i, r in enumerate(responses) if r['status'] == 'success']
        random.shuffle(anonymized)
        
        anon_text = "\n\n".join([f"**Response {label}:**\n{text}" for label, text in anonymized])
        
        # Each persona votes
        voting_tasks = []
        for response in responses:
            if response['status'] == 'success':
                voting_tasks.append(self._get_hive_vote(response['model'], anon_text, message))
        
        vote_results = await asyncio.gather(*voting_tasks, return_exceptions=True)
        
        # Count votes
        label_to_model = {chr(65 + i): r['model'] for i, r in enumerate(responses) if r['status'] == 'success'}
        
        for vote in vote_results:
            if isinstance(vote, str) and vote in label_to_model:
                votes[label_to_model[vote]] += 1
        
        return votes
    
    async def _get_elite_vote(self, model_name, anonymized_responses, question):
        """Get vote from an Elite model"""
        try:
            prompt = f"""You are voting for the best response to this question:
"{question}"

Here are the anonymized responses:

{anonymized_responses}

Vote for the BEST response by returning ONLY the letter (A, B, or C). Consider:
- Accuracy and depth
- Practical actionability
- Alignment with user's needs

Your vote (single letter only):"""
            
            # Use hardcoded API model names (like council.py does)
            if 'GPT' in model_name or 'gpt' in model_name:
                client = AsyncOpenAI(api_key=self.config['api_keys']['openai'])
                response = await client.chat.completions.create(
                    model="gpt-5",
                    messages=[{"role": "user", "content": prompt}],
                    max_completion_tokens=10
                )
                vote = response.choices[0].message.content.strip()[:1]
            elif 'Claude' in model_name or 'claude' in model_name:
                client = AsyncAnthropic(api_key=self.config['api_keys']['anthropic'])
                # Filter empty messages from history
                messages = [{"role": "user", "content": prompt}]
                response = await client.messages.create(
                    model="claude-haiku-4-5",
                    max_tokens=10,
                    messages=messages
                )
                vote = response.content[0].text.strip()[:1]
            else:  # Gemini
                try:
                    genai.configure(api_key=self.config['api_keys']['google'])
                    model = genai.GenerativeModel("gemini-3-pro-preview")
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(None, lambda: model.generate_content(prompt))
                    
                    # Validate response
                    if not response or not hasattr(response, 'text') or not response.text:
                        print(f"⚠️ Gemini returned empty response for {model_name}, using fallback")
                        return "A"  # Fallback vote
                    
                    vote = response.text.strip()[:1]
                except Exception as gemini_error:
                    print(f"⚠️ Gemini vote error for {model_name}: {gemini_error}, using fallback")
                    return "A"  # Fallback vote
            
            return vote
        except Exception as e:
            print(f"❌ Elite vote failed for {model_name}: {e}")
            return None
    
    async def _get_hive_vote(self, persona_name, anonymized_responses, question):
        """Get vote from a Hive persona"""
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.config['api_keys']['openrouter']
            )
            
            prompt = f"""You are {persona_name} voting for the best response to: "{question}"

{anonymized_responses}

Vote for the BEST response (A-F). Return ONLY the letter.
Your vote:"""
            
            response = await client.chat.completions.create(
                model="deepseek/deepseek-v3.2-speciale",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10
            )
            
            vote = response.choices[0].message.content.strip()[:1]
            return vote
        except Exception as e:
            print(f"❌ Hive vote failed for {persona_name}: {e}")
            return None
    
    async def _refine_answer(self, model_name, original_response, question, context, council_type):
        """Winner refines their answer with additional info"""
        try:
            prompt = f"""You won the {council_type} council vote with this response:

"{original_response}"

Original question: "{question}"

You may now REFINE and EXPAND your answer with additional insights. Keep it concise but add valuable details.

Refined response:"""
            
            if council_type == "elite":
                if 'GPT' in model_name or 'gpt' in model_name:
                    client = AsyncOpenAI(api_key=self.config['api_keys']['openai'])
                    response = await client.chat.completions.create(
                        model="gpt-5",
                        messages=[{"role": "user", "content": prompt}],
                        max_completion_tokens=500
                    )
                    return response.choices[0].message.content
                elif 'Claude' in model_name or 'claude' in model_name:
                    client = AsyncAnthropic(api_key=self.config['api_keys']['anthropic'])
                    response = await client.messages.create(
                        model="claude-haiku-4-5",
                        max_tokens=500,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return response.content[0].text
                else:  # Gemini
                    try:
                        genai.configure(api_key=self.config['api_keys']['google'])
                        model = genai.GenerativeModel("gemini-3-pro-preview")
                        loop = asyncio.get_event_loop()
                        response = await loop.run_in_executor(None, lambda: model.generate_content(prompt))
                        
                        # Validate response
                        if not response or not hasattr(response, 'text') or not response.text:
                            print(f"⚠️ Gemini refinement returned empty, using original")
                            return original_response
                        
                        return response.text
                    except Exception as gemini_error:
                        print(f"⚠️ Gemini refinement error: {gemini_error}, using original")
                        return original_response
            else:  # hive
                client = AsyncOpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=self.config['api_keys']['openrouter']
                )
                response = await client.chat.completions.create(
                    model="deepseek/deepseek-v3.2-speciale",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500
                )
                return response.choices[0].message.content
                
        except Exception as e:
            print(f"❌ Refinement failed: {e}")
            return original_response  # Return original if refinement fails
    
    async def _mega_chairman_synthesis(self, question, elite_result, hive_result, context):
        """Ultimate chairman synthesizes Elite and Hive winners"""
        
        # Get mega chairman model from config
        mega_chairman_model = self.config.get('mega_chairman_model', 'gemini-3-pro-preview')
        
        print(f"👑 Mega Chairman ({mega_chairman_model}): Synthesizing...")
        
        prompt = f"""You are the MEGA CHAIRMAN - the ultimate arbiter.

Two expert councils have deliberated on this question:
"{question}"

ELITE COUNCIL WINNER ({elite_result['winner_model']}):
{elite_result['winner_response']}

HIVE COUNCIL WINNER ({hive_result['winner_model']}):
{hive_result['winner_response']}

YOUR TASK:
1. Synthesize both expert verdicts
2. Identify consensus and conflicts
3. Make the FINAL decision that serves Jesse's best interests
4. Be direct, pragmatic, and actionable

You are Jesse's ultimate strategic partner. Provide the definitive answer.

Format in Markdown."""
        
        try:
            # Use configured chairman model
            if 'gpt' in mega_chairman_model.lower():
                client = AsyncOpenAI(api_key=self.config['api_keys']['openai'])
                response = await client.chat.completions.create(
                    model=mega_chairman_model,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content
            elif 'claude' in mega_chairman_model.lower():
                client = AsyncAnthropic(api_key=self.config['api_keys']['anthropic'])
                response = await client.messages.create(
                    model=mega_chairman_model,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            elif 'grok' in mega_chairman_model.lower():
                client = AsyncOpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=self.config['api_keys']['openrouter']
                )
                response = await client.chat.completions.create(
                    model=mega_chairman_model,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content
            else:  # Gemini (default)
                genai.configure(api_key=self.config['api_keys']['google'])
                model = genai.GenerativeModel(mega_chairman_model)
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, lambda: model.generate_content(prompt))
                return response.text
        except Exception as e:
            return f"**Mega Chairman Error:** {str(e)}"
