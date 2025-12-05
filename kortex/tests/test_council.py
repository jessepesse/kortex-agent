import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kortex.ai.council import CouncilService
from kortex import data

async def test_council():
    print("🚀 Testing Council Mode...")
    
    # Load context
    context = data.load_all_context()
    print(f"Loaded context with keys: {list(context.keys())}")
    
    service = CouncilService()
    
    message = "I'm feeling low energy. What should I do?"
    history = []
    
    print(f"\nQuery: {message}")
    
    result = await service.get_council_response(message, history, context)
    
    print("\n--- Result ---")
    print(result)

if __name__ == "__main__":
    asyncio.run(test_council())
