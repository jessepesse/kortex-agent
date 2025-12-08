"""Data operations for Kortex Agent"""

from __future__ import annotations

import json
import time
import uuid
import os
import re
from pathlib import Path
from typing import Any, Optional

from .config import DATA_DIR
from .logging import get_logger

logger = get_logger(__name__)


# Type aliases
JsonDict = dict[str, Any]
ConversationMessage = dict[str, str]


# =============================================================================
# DEFAULT DATA STRUCTURES
# =============================================================================

DEFAULT_DATA: dict[str, JsonDict] = {
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
        "budgets": {"monthly": {}},
        "transactions": [],
        "notes": []
    },
    "routines": {
        "daily": {"morning": [], "evening": []},
        "weekly": [],
        "habits": []
    },
    "values": {
        "core_values": [],
        "principles": [],
        "priorities": []
    },
    "active_projects": {"projects": []},
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

def get_all_json_files() -> list[str]:
    """Dynamically scan the data directory for all JSON files."""
    DATA_DIR.mkdir(exist_ok=True)
    json_files = [f.name for f in DATA_DIR.glob("*.json")]
    json_files.sort()
    return json_files


def validate_filename(filename: str) -> Path:
    """Validate and resolve filename to ensure it stays within DATA_DIR.
    
    Prevents Path Traversal attacks by enforcing basename.
    """
    # Draconian whitelist: Only allow alphanumeric, dots, underscores, dashes
    # CodeQL: Input is strictly validated against a regex allowlist. 
    # Path traversal characters (/, \, ..) are explicitly rejected.
    if not re.match(r'^[a-zA-Z0-9_.-]+$', filename):
        # Fallback: try basename and check again, or just reject
        safe_name = os.path.basename(filename)
        if not re.match(r'^[a-zA-Z0-9_.-]+$', safe_name):
            raise ValueError(f"Invalid filename: {filename}. Only alphanumeric, dot, underscore, dash allowed.")
        filename = safe_name

    filepath = (DATA_DIR / filename).resolve()
    
    # Verify the resolved path starts with DATA_DIR
    if not str(filepath).startswith(str(DATA_DIR.resolve())):
        raise ValueError("Access denied: path points outside safe directory.")
        
    return filepath


def load_json_file(filename: str) -> JsonDict:
    """Load a JSON file from the data directory.
    
    If the file doesn't exist, creates it with default data.
    """
    try:
        filepath = validate_filename(filename)
    except ValueError as e:
        logger.error(str(e))
        return {}
        
    DATA_DIR.mkdir(exist_ok=True)
    
    # Extract key from basename (handle .json extension safely)
    key = Path(filename).stem
    default_data = DEFAULT_DATA.get(key, {})
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        with open(filepath, 'w') as f:
            json.dump(default_data, f, indent=2)
        return default_data
    except json.JSONDecodeError:
        logger.warning(f"Could not parse {filename}. Using default data.")
        return default_data


def save_json_file(filename: str, data: JsonDict) -> str:
    """Save data to a JSON file in the data directory."""
    try:
        filepath = validate_filename(filename)
    except ValueError as e:
        return f"Error: {str(e)}"
        
    DATA_DIR.mkdir(exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    return f"✓ Updated {filename}"


def load_all_context() -> dict[str, JsonDict]:
    """Dynamically load all JSON files from the data directory."""
    if not get_all_json_files():
        initialize_data()
    
    context: dict[str, JsonDict] = {}
    for filename in get_all_json_files():
        key = filename.replace('.json', '')
        context[key] = load_json_file(filename)
    
    return context


def initialize_data() -> None:
    """Create all default data files if they don't exist."""
    DATA_DIR.mkdir(exist_ok=True)
    
    for key, default in DEFAULT_DATA.items():
        filepath = DATA_DIR / f"{key}.json"
        if not filepath.exists():
            with open(filepath, 'w') as f:
                json.dump(default, f, indent=2)
            logger.info(f"Created {key}.json with default data")


# =============================================================================
# CONVERSATION MANAGEMENT
# =============================================================================

def get_conversations_dir() -> Path:
    """Get the directory for storing conversations."""
    conv_dir = DATA_DIR / "conversations"
    conv_dir.mkdir(parents=True, exist_ok=True)
    return conv_dir


def generate_chat_id() -> str:
    """Generate a unique chat ID based on timestamp and UUID."""
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8]
    return f"{timestamp}_{unique_id}"


def validate_chat_id(chat_id: str) -> str:
    """Validate chat ID format to prevent path traversal.
    
    Chat IDs should be alphanumeric with underscores.
    """
    if not chat_id or not chat_id.replace('_', '').isalnum():
        raise ValueError(f"Invalid chat ID: {chat_id}")
    return chat_id


def save_conversation(
    chat_id: str, 
    messages: list[ConversationMessage], 
    title: Optional[str] = None
) -> str:
    """Save a conversation to a JSON file."""
    validate_chat_id(chat_id)
    conv_dir = get_conversations_dir()
    filepath = conv_dir / f"{chat_id}.json"
    
    # Preserve pinned status if conversation exists
    existing_pinned = False
    if filepath.exists():
        try:
            with open(filepath, 'r') as f:
                existing_data = json.load(f)
                existing_pinned = existing_data.get('pinned', False)
        except Exception:
            pass
    
    data: JsonDict = {
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


def load_conversation(chat_id: str) -> Optional[JsonDict]:
    """Load a conversation by ID."""
    try:
        validate_chat_id(chat_id)
    except ValueError:
        return None
        
    conv_dir = get_conversations_dir()
    filepath = conv_dir / f"{chat_id}.json"
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def list_conversations() -> list[JsonDict]:
    """List all saved conversations, sorted by newest first."""
    conv_dir = get_conversations_dir()
    conversations: list[JsonDict] = []
    
    for filepath in conv_dir.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                messages = data.get("messages", [])
                preview = messages[-1].get("content", "")[:50] if messages else ""
                
                conversations.append({
                    "id": data.get("id"),
                    "title": data.get("title", "Untitled"),
                    "timestamp": data.get("timestamp", 0),
                    "lastModified": data.get("lastModified", data.get("timestamp", 0)),
                    "pinned": data.get("pinned", False),
                    "preview": preview
                })
        except Exception:
            continue
            
    conversations.sort(key=lambda x: x["timestamp"], reverse=True)
    return conversations


def delete_conversation(chat_id: str) -> bool:
    """Delete a conversation by ID."""
    try:
        validate_chat_id(chat_id)
    except ValueError as e:
        logger.error(str(e))
        return False
        
    conv_dir = get_conversations_dir()
    filepath = conv_dir / f"{chat_id}.json"
    
    try:
        if filepath.exists():
            filepath.unlink()
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting conversation {chat_id}: {e}")
        return False


def toggle_pin(chat_id: str) -> Optional[bool]:
    """Toggle pinned status of a conversation."""
    try:
        validate_chat_id(chat_id)
    except ValueError as e:
        logger.error(str(e))
        return None
        
    conv_dir = get_conversations_dir()
    filepath = conv_dir / f"{chat_id}.json"
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        data['pinned'] = not data.get('pinned', False)
        data['lastModified'] = int(time.time())
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data['pinned']
    except FileNotFoundError:
        return None
    except Exception as e:
        logger.error(f"Error toggling pin for {chat_id}: {e}")
        return None
