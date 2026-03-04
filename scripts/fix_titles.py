#!/usr/bin/env python3
"""
Fix missing conversation titles (New Chat) by generating them with Gemini 2.5 Flash Lite
Can be run manually or as a background task
"""

import os
import sys
import json
from openai import OpenAI
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kortex.config import load_config


def fix_conversation_titles(dry_run=False):
    """Fix all conversations with 'New Chat' title"""
    
    # Load config
    config = load_config()
    api_key = config['api_keys'].get('openrouter')
    
    if not api_key:
        print("❌ No OpenRouter API key found")
        return
    
    or_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )
    
    # Find all conversation files
    conv_dir = Path(__file__).parent.parent / 'data' / 'conversations'
    if not conv_dir.exists():
        print(f"❌ Conversations directory not found: {conv_dir}")
        return
    
    conv_files = list(conv_dir.glob('*.json'))
    print(f"📂 Found {len(conv_files)} conversation files")
    
    fixed_count = 0
    skipped_count = 0
    
    for conv_file in conv_files:
        try:
            with open(conv_file, 'r', encoding='utf-8') as f:
                conv_data = json.load(f)
            
            # Check if title is "New Chat" or missing
            current_title = conv_data.get('title', 'New Chat')
            
            if current_title and current_title != 'New Chat':
                skipped_count += 1
                continue
            
            # Get first user message
            messages = conv_data.get('messages', [])
            if not messages:
                print(f"⚠️  {conv_file.name}: No messages, skipping")
                skipped_count += 1
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
                print(f"⚠️  {conv_file.name}: No user message found, skipping")
                skipped_count += 1
                continue
            
            # Generate title
            title_prompt = f"""Generate a short, concise title (max 40 characters) for this conversation.
User message: {user_msg[:500]}
{f"AI response: {ai_response[:200]}" if ai_response else ""}

Respond with ONLY the title in Finnish, no quotes or extra text. Be specific and descriptive."""
            
            try:
                title_response = or_client.chat.completions.create(
                    model="google/gemini-3.1-flash-lite-preview",
                    messages=[{"role": "user", "content": title_prompt}],
                    max_tokens=50
                )
                
                if title_response.choices[0].message.content:
                    new_title = title_response.choices[0].message.content.strip()[:50]
                    
                    if dry_run:
                        print(f"🔍 {conv_file.name}: Would update '{current_title}' → '{new_title}'")
                    else:
                        # Update title
                        conv_data['title'] = new_title
                        
                        # Save back
                        with open(conv_file, 'w', encoding='utf-8') as f:
                            json.dump(conv_data, f, ensure_ascii=False, indent=2)
                        
                        print(f"✅ {conv_file.name}: Updated to '{new_title}'")
                    
                    fixed_count += 1
                else:
                    print(f"⚠️  {conv_file.name}: Gemini returned empty response")
                    skipped_count += 1
                    
            except Exception as e:
                print(f"❌ {conv_file.name}: Failed to generate title: {e}")
                skipped_count += 1
                
        except Exception as e:
            print(f"❌ {conv_file.name}: Error reading file: {e}")
            skipped_count += 1
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Fixed: {fixed_count}")
    print(f"   ⏭️  Skipped: {skipped_count}")
    print(f"   📁 Total: {len(conv_files)}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix missing conversation titles')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')
    
    args = parser.parse_args()
    
    print("🔧 Kortex Agent Title Fixer")
    print("=" * 50)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")
    
    fix_conversation_titles(dry_run=args.dry_run)
