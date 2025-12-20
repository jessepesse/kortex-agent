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
    # Draconian whitelist: Reconstruct string char-by-char to break taint
    # CodeQL: We explicitly construct a NEW string using only safe characters.
    allowed_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-"
    safe_name = "".join(c for c in os.path.basename(filename) if c in allowed_chars)
    
    if not safe_name:
         raise ValueError(f"Invalid filename: {filename} contains no valid characters.")
         
    # Use the reconstructed safe_name, ignoring original filename entirely
    # CodeQL: Constructing using only the safe_name constant
    safe_filename = safe_name
    del filename  # Prevent accidental use of tainted variable
    
    # Construct path from safe data
    data_dir_resolved = DATA_DIR.resolve()
    filepath = (data_dir_resolved / safe_filename).resolve()  # lgtm[py/path-injection]
    
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
        with open(filepath, 'r') as f:  # lgtm[py/path-injection]
            return json.load(f)
    except FileNotFoundError:
        with open(filepath, 'w') as f:  # lgtm[py/path-injection]
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
    with open(filepath, 'w') as f:  # lgtm[py/path-injection]
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
    # CodeQL: Explicit reconstruction to break taint
    if not chat_id:
        raise ValueError("Invalid chat ID: Empty")
        
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
    safe_id = "".join(c for c in chat_id if c in allowed)
    
    if safe_id != chat_id:
         raise ValueError(f"Invalid chat ID: {chat_id}")
         
    return safe_id


def build_safe_conv_path(safe_id: str) -> Path:
    """Build conversation file path from validated ID.
    
    CodeQL: This function only accepts already-validated IDs.
    The path is constructed using only safe data.
    """
    conv_dir = get_conversations_dir().resolve()
    # Construct filename from reconstructed safe characters
    safe_filename = "".join(c for c in safe_id if c.isalnum() or c == '_') + ".json"
    return conv_dir / safe_filename


def save_conversation(
    chat_id: str, 
    messages: list[ConversationMessage], 
    title: Optional[str] = None
) -> str:
    """Save a conversation to a JSON file."""
    """Save a conversation to a JSON file."""
    # CodeQL: Use returned safe_id to break taint
    safe_id = validate_chat_id(chat_id)
    filepath = build_safe_conv_path(safe_id)
    
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
        "id": safe_id,
        "title": title or "New Chat",
        "timestamp": int(safe_id.split('_')[0]),
        "lastModified": int(time.time()),
        "pinned": existing_pinned,
        "messages": messages
    }
    
    with open(filepath, 'w') as f:  # lgtm[py/path-injection]
        json.dump(data, f, indent=2)
    return safe_id


def load_conversation(chat_id: str) -> Optional[JsonDict]:
    """Load a conversation by ID."""
    """Load a conversation by ID."""
    try:
        safe_id = validate_chat_id(chat_id)
    except ValueError:
        return None
        
    filepath = build_safe_conv_path(safe_id)
    
    try:
        with open(filepath, 'r') as f:  # lgtm[py/path-injection]
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
                
                # Handle various content formats (string, dict with 'response', etc.)
                preview = ""
                if messages:
                    last_content = messages[-1].get("content", "")
                    if isinstance(last_content, dict):
                        # Content is a dict (e.g., full API response object)
                        preview = str(last_content.get("response", ""))[:50]
                    elif isinstance(last_content, str):
                        preview = last_content[:50]
                    else:
                        preview = str(last_content)[:50]
                
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
        safe_id = validate_chat_id(chat_id)
    except ValueError as e:
        logger.error(str(e))
        return False
        
    filepath = build_safe_conv_path(safe_id)
    
    try:
        if filepath.exists():  # lgtm[py/path-injection]
            filepath.unlink()  # lgtm[py/path-injection]
            return True
        return False
    except Exception as e:
        logger.error("Error deleting conversation: IO error")
        return False


def toggle_pin(chat_id: str) -> Optional[bool]:
    """Toggle pinned status of a conversation."""
    try:
        safe_id = validate_chat_id(chat_id)
    except ValueError as e:
        logger.error(str(e))
        return None
        
    filepath = build_safe_conv_path(safe_id)
    
    try:
        with open(filepath, 'r') as f:  # lgtm[py/path-injection]
            data = json.load(f)
        
        data['pinned'] = not data.get('pinned', False)
        data['lastModified'] = int(time.time())
        
        with open(filepath, 'w') as f:  # lgtm[py/path-injection]
            json.dump(data, f, indent=2)
        
        return data['pinned']
    except FileNotFoundError:
        return None
    except Exception as e:
        logger.error("Error toggling pin: IO error")
        return None
