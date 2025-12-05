"""Data operations for Kortex Agent"""

import json
from pathlib import Path
from .config import DATA_DIR


# =============================================================================
# DEFAULT DATA STRUCTURES
# =============================================================================
# These are used when creating new data files for first-time users

DEFAULT_DATA = {
    "profile": {
        "name": "",
        "location": "",
        "timezone": "Europe/Helsinki",
        "language": "Finnish",
        "occupation": "",
        "bio": "",
        "preferences": {
            "communication_style": "direct",
            "detail_level": "balanced"
        }
    },
    "health": {
        "current_state": {
            "physical": "",
            "mental": "",
            "energy": 5,
            "sleep_quality": "",
            "last_updated": ""
        },
        "conditions": [],
        "medications": [],
        "exercise_log": [],
        "notes": []
    },
    "goals": {
        "short_term": [],
        "long_term": [],
        "completed": []
    },
    "finance": {
        "accounts": [],
        "budgets": {
            "monthly": {}
        },
        "transactions": [],
        "notes": []
    },
    "routines": {
        "daily": {
            "morning": [],
            "evening": []
        },
        "weekly": [],
        "habits": []
    },
    "values": {
        "core_values": [],
        "principles": [],
        "priorities": []
    },
    "active_projects": {
        "projects": []
    },
    "tech_inventory": {
        "devices": [],
        "subscriptions": [],
        "wishlist": []
    },
    "meal_rotation": {
        "meals": [],
        "favorites": [],
        "weekly_plan": {}
    },
    "pantry_staples": {
        "staples": [],
        "shopping_list": []
    }
}


# =============================================================================
# DATA FILE OPERATIONS
# =============================================================================

def get_all_json_files():
    """Dynamically scan the data directory for all JSON files."""
    DATA_DIR.mkdir(exist_ok=True)
    json_files = [f.name for f in DATA_DIR.glob("*.json")]
    json_files.sort()
    return json_files


def load_json_file(filename):
    """Load a JSON file from the data directory.
    
    If the file doesn't exist, creates it with default data.
    """
    filepath = DATA_DIR / filename
    DATA_DIR.mkdir(exist_ok=True)
    
    # Get default data for this file type
    key = filename.replace('.json', '')
    default_data = DEFAULT_DATA.get(key, {})
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Create file with default data
        with open(filepath, 'w') as f:
            json.dump(default_data, f, indent=2)
        return default_data
    except json.JSONDecodeError:
        print(f"Warning: Could not parse {filename}. Using default data.")
        return default_data


def save_json_file(filename, data):
    """Save data to a JSON file in the data directory."""
    filepath = DATA_DIR / filename
    DATA_DIR.mkdir(exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    return f"✓ Updated {filename}"


def load_all_context():
    """Dynamically load all JSON files from the data directory.
    
    If no files exist, initializes with default data files.
    """
    # Initialize default files if data directory is empty
    if not get_all_json_files():
        initialize_data()
    
    context = {}
    json_files = get_all_json_files()
    
    for filename in json_files:
        key = filename.replace('.json', '')
        context[key] = load_json_file(filename)
    
    return context


def initialize_data():
    """Create all default data files if they don't exist.
    
    Called automatically on first run.
    """
    DATA_DIR.mkdir(exist_ok=True)
    
    for key, default in DEFAULT_DATA.items():
        filepath = DATA_DIR / f"{key}.json"
        if not filepath.exists():
            with open(filepath, 'w') as f:
                json.dump(default, f, indent=2)
            print(f"Created {key}.json with default data")


# Conversation Management

def get_conversations_dir():
    """Get the directory for storing conversations."""
    conv_dir = DATA_DIR / "conversations"
    conv_dir.mkdir(parents=True, exist_ok=True)
    return conv_dir


def generate_chat_id():
    """Generate a unique chat ID based on timestamp and UUID."""
    import time
    import uuid
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8]
    return f"{timestamp}_{unique_id}"


def save_conversation(chat_id, messages, title=None):
    """Save a conversation to a JSON file."""
    conv_dir = get_conversations_dir()
    filepath = conv_dir / f"{chat_id}.json"
    
    # Check if conversation exists to preserve pinned status
    existing_pinned = False
    if filepath.exists():
        try:
            with open(filepath, 'r') as f:
                existing_data = json.load(f)
                existing_pinned = existing_data.get('pinned', False)
        except:
            pass
    
    import time
    data = {
        "id": chat_id,
        "title": title or "New Chat",
        "timestamp": int(chat_id.split('_')[0]),
        "lastModified": int(time.time()),
        "pinned": existing_pinned,
        "messages": messages
    }
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    return chat_id


def load_conversation(chat_id):
    """Load a conversation by ID."""
    conv_dir = get_conversations_dir()
    filepath = conv_dir / f"{chat_id}.json"
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def list_conversations():
    """List all saved conversations, sorted by newest first."""
    conv_dir = get_conversations_dir()
    conversations = []
    
    for filepath in conv_dir.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                conversations.append({
                    "id": data.get("id"),
                    "title": data.get("title", "Untitled"),
                    "timestamp": data.get("timestamp", 0),
                    "lastModified": data.get("lastModified", data.get("timestamp", 0)),
                    "pinned": data.get("pinned", False),
                    "preview": data.get("messages", [])[-1].get("content", "")[:50] if data.get("messages") else ""
                })
        except Exception:
            continue
            
    # Sort by timestamp descending (newest first)
    conversations.sort(key=lambda x: x["timestamp"], reverse=True)
    return conversations


def delete_conversation(chat_id):
    """Delete a conversation by ID."""
    conv_dir = get_conversations_dir()
    filepath = conv_dir / f"{chat_id}.json"
    
    try:
        if filepath.exists():
            filepath.unlink()
            return True
        return False
    except Exception as e:
        print(f"Error deleting conversation {chat_id}: {e}")
        return False


def toggle_pin(chat_id):
    """Toggle pinned status of a conversation"""
    conv_dir = get_conversations_dir()
    filepath = conv_dir / f"{chat_id}.json"
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Toggle pinned status
        data['pinned'] = not data.get('pinned', False)
        
        # Update lastModified
        import time
        data['lastModified'] = int(time.time())
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data['pinned']
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error deleting conversation {chat_id}: {e}")
        return False
