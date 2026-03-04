"""
Background task for fixing missing conversation titles
Runs periodically to ensure all conversations have proper titles
"""

import threading
import time
import os
import json
import logging
from openai import OpenAI
from pathlib import Path
from kortex.config import load_config

logger = logging.getLogger(__name__)


class TitleFixerService:
    """Background service to fix missing conversation titles"""
    
    def __init__(self, interval_hours=24):
        """
        Initialize the title fixer service
        
        Args:
            interval_hours: How often to run the fixer (default: 24 hours)
        """
        self.interval_hours = interval_hours
        self.running = False
        self.thread = None
        
    def start(self):
        """Start the background service"""
        if self.running:
            logger.warning("Title fixer already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("Title fixer started (runs every %d hours)", self.interval_hours)
    
    def stop(self):
        """Stop the background service"""
        self.running = False
        if self.thread:
            logger.info("Title fixer stopped")
    
    def _run_loop(self):
        """Main loop that runs periodically"""
        # Run immediately on startup
        self._fix_titles()
        
        # Then run every N hours
        while self.running:
            time.sleep(self.interval_hours * 3600)  # Convert hours to seconds
            if self.running:  # Check again after sleep
                self._fix_titles()
    
    def _fix_titles(self):
        """Fix all conversations with 'New Chat' title"""
        try:
            logger.info("Running title fixer...")
            
            # Load config
            config = load_config()
            api_key = config['api_keys'].get('openrouter')
            
            if not api_key:
                logger.warning("No OpenRouter API key found, skipping title fix")
                return
            
            or_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key
            )
            
            # Find all conversation files
            conv_dir = Path(__file__).parent.parent / 'data' / 'conversations'
            if not conv_dir.exists():
                return
            
            conv_files = list(conv_dir.glob('*.json'))
            fixed_count = 0
            
            for conv_file in conv_files:
                try:
                    with open(conv_file, 'r', encoding='utf-8') as f:
                        conv_data = json.load(f)
                    
                    # Check if title is "New Chat" or missing
                    current_title = conv_data.get('title', 'New Chat')
                    
                    if current_title and current_title != 'New Chat':
                        continue
                    
                    # Get first user message
                    messages = conv_data.get('messages', [])
                    if not messages:
                        continue
                    
                    # Find first user message and AI response
                    user_msg = None
                    ai_response = None
                    
                    for i, msg in enumerate(messages):
                        if msg.get('role') == 'user' and not user_msg:
                            user_msg = msg.get('content', '')
                        elif msg.get('role') == 'assistant' and user_msg and not ai_response:
                            ai_response = msg.get('content', '')
                            break
                    
                    if not user_msg:
                        continue
                    
                    # Generate title
                    title_prompt = f"""Generate a short, concise title (max 40 characters) for this conversation.
User message: {user_msg[:500]}
{f"AI response: {ai_response[:200]}" if ai_response else ""}

Respond with ONLY the title in Finnish, no quotes or extra text. Be specific and descriptive."""
                    
                    title_response = or_client.chat.completions.create(
                        model="google/gemini-3.1-flash-lite-preview",
                        messages=[{"role": "user", "content": title_prompt}],
                        max_tokens=50
                    )
                    
                    if title_response.choices[0].message.content:
                        new_title = title_response.choices[0].message.content.strip()[:50]
                        
                        # Update title
                        conv_data['title'] = new_title
                        
                        # Save back
                        with open(conv_file, 'w', encoding='utf-8') as f:
                            json.dump(conv_data, f, ensure_ascii=False, indent=2)
                        
                        logger.info("Fixed: %s → '%s'", conv_file.name, new_title)
                        fixed_count += 1
                        
                except Exception as e:
                    # Silently skip errors in background task
                    pass
            
            if fixed_count > 0:
                logger.info("Title fixer completed: %d titles fixed", fixed_count)
            else:
                logger.info("Title fixer: All titles OK")
                
        except Exception as e:
            logger.error("Title fixer error: %s", e)


# Singleton instance
_title_fixer_instance = None

def get_title_fixer(interval_hours=24):
    """Get or create the singleton title fixer instance"""
    global _title_fixer_instance
    if _title_fixer_instance is None:
        _title_fixer_instance = TitleFixerService(interval_hours=interval_hours)
    return _title_fixer_instance
