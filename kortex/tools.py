"""Function calling tools for Kortex Agent"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .data import load_json_file, save_json_file, get_all_json_files
from .config import DATA_DIR
from .logging import get_logger

# Type aliases
JsonDict = dict[str, Any]

logger = get_logger(__name__)


def update_profile(data: dict) -> str:
    """Update profile information.
    NOTE: Do NOT store health, energy, or mental health data here. Use update_health instead.
    """
    import json
    logger.debug(f"update_profile called with data type: {type(data)}, value: {data}")
    
    # Handle case where data might not be a dict
    if not isinstance(data, dict):
        logger.error(f"Data is not a dict! Type: {type(data)}")
        return f"Error: Expected dict, got {type(data).__name__}"
    
    existing = load_json_file("profile.json")
    merged = {**existing, **data}
    save_json_file("profile.json", merged)
    return "Profile updated"


def update_values(data: dict) -> str:
    """Update core values and anti-values"""
    existing = load_json_file("values.json")
    merged = {**existing, **data}
    save_json_file("values.json", merged)
    return "Values updated"


def update_health(data: dict) -> str:
    """Update health metrics, energy levels, and mental health status."""
    existing = load_json_file("health.json")
    merged = {**existing, **data}
    save_json_file("health.json", merged)
    return "Health updated"


def update_tech_inventory(data: dict) -> str:
    """Update tech inventory"""
    existing = load_json_file("tech_inventory.json")
    merged = {**existing, **data}
    save_json_file("tech_inventory.json", merged)
    return "Tech inventory updated"


def update_active_projects(data: dict) -> str:
    """Update active projects"""
    existing = load_json_file("active_projects.json")
    merged = {**existing, **data}
    save_json_file("active_projects.json", merged)
    return "Projects updated"


def update_routines(data: dict) -> str:
    """Update routines"""
    existing = load_json_file("routines.json")
    merged = {**existing, **data}
    save_json_file("routines.json", merged)
    return "Routines updated"


def update_pantry_staples(data: dict) -> str:
    """Update pantry inventory"""
    existing = load_json_file("pantry_staples.json")
    merged = {**existing, **data}
    save_json_file("pantry_staples.json", merged)
    return "Pantry updated"


def update_meal_rotation(data: dict) -> str:
    """Update meal rotation"""
    existing = load_json_file("meal_rotation.json")
    merged = {**existing, **data}
    save_json_file("meal_rotation.json", merged)
    return "Meals updated"


def update_finance(data: dict) -> str:
    """Update finance data"""
    existing = load_json_file("finance.json")
    merged = {**existing, **data}
    save_json_file("finance.json", merged)
    return "Finance updated"


def create_data_file(filename: str, initial_data: dict, description: str = "") -> str:
    """Create a new JSON data file"""
    if not filename.endswith('.json'):
        filename = f"{filename}.json"
    
    if '/' in filename or '\\' in filename or '..' in filename:
        return f"Error: Invalid filename"
    
    filepath = DATA_DIR / filename
    if filepath.exists():
        return f"Error: File exists"
    
    try:
        with open(filepath, 'w') as f:
            import json
            json.dump(initial_data, f, indent=2)
        return f"✓ Created {filename}"
    except Exception as e:
        return f"Error: {str(e)}"


def update_data_file(filename: str, data: dict) -> str:
    """Update any data file"""
    if not filename.endswith('.json'):
        filename = f"{filename}.json"
    
    # Security check: prevent directory traversal
    if '/' in filename or '\\' in filename or '..' in filename:
        return f"Error: Invalid filename"
    
    filepath = DATA_DIR / filename
    if not filepath.exists():
        return f"Error: File {filename} does not exist"
    
    try:
        existing = load_json_file(filename)
        # Deep merge or simple update? Simple update for now
        merged = {**existing, **data}
        save_json_file(filename, merged)
        return f"Updated {filename}"
    except Exception as e:
        return f"Error updating {filename}: {str(e)}"


def list_data_files() -> str:
    """List all available data files"""
    try:
        files = get_all_json_files()
        return f"Available data files: {', '.join(files)}"
    except Exception as e:
        return f"Error listing files: {str(e)}"


# Tool functions mapping
TOOL_FUNCTIONS = {
    "update_profile": update_profile,
    "update_values": update_values,
    "update_health": update_health,
    "update_tech_inventory": update_tech_inventory,
    "update_active_projects": update_active_projects,
    "update_routines": update_routines,
    "update_pantry_staples": update_pantry_staples,
    "update_meal_rotation": update_meal_rotation,
    "update_finance": update_finance,
    "create_data_file": create_data_file,
    "update_data_file": update_data_file,
    "list_data_files": list_data_files,
}

# OpenAI Tool Definitions
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "update_profile",
            "description": "Update user profile information (name, age, location, focus, etc.). Do NOT use for health/energy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {"type": "object", "description": "Profile data to update"}
                },
                "required": ["data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_values",
            "description": "Update core values and anti-values",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {"type": "object", "description": "Values data to update"}
                },
                "required": ["data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_health",
            "description": "Update health metrics, energy levels, mental health, goals, and current state",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {"type": "object", "description": "Health data to update"}
                },
                "required": ["data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_tech_inventory",
            "description": "Update tech inventory (hardware, software, wishlist)",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {"type": "object", "description": "Tech inventory data to update"}
                },
                "required": ["data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_active_projects",
            "description": "Update active projects and tasks",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {"type": "object", "description": "Project data to update"}
                },
                "required": ["data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_routines",
            "description": "Update weekly routines and templates",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {"type": "object", "description": "Routines data to update"}
                },
                "required": ["data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_pantry_staples",
            "description": "Update pantry inventory",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {"type": "object", "description": "Pantry data to update"}
                },
                "required": ["data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_meal_rotation",
            "description": "Update meal rotation and recipes",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {"type": "object", "description": "Meal data to update"}
                },
                "required": ["data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_finance",
            "description": "Update financial data (budget, subscriptions)",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {"type": "object", "description": "Finance data to update"}
                },
                "required": ["data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_data_file",
            "description": "Create a new JSON data file for a new category",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Name of the file (e.g., 'books.json')"},
                    "initial_data": {"type": "object", "description": "Initial data structure"},
                    "description": {"type": "string", "description": "Description of the file's purpose"}
                },
                "required": ["filename", "initial_data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_data_file",
            "description": "Update any generic data file",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Name of the file to update"},
                    "data": {"type": "object", "description": "Data to merge into the file"}
                },
                "required": ["filename", "data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_data_files",
            "description": "List all available data files to check what categories exist",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

# Gemini-native Tool Definitions (without OpenAI wrapper)
GEMINI_TOOL_DEFINITIONS = [
    {
        "name": "update_profile",
        "description": "Update user profile information (name, age, location, focus, etc.). Do NOT use for health/energy.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "data": {"type": "OBJECT", "description": "Profile data to update"}
            },
            "required": ["data"]
        }
    },
    {
        "name": "update_values",
        "description": "Update core values and anti-values",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "data": {"type": "OBJECT", "description": "Values data to update"}
            },
            "required": ["data"]
        }
    },
    {
        "name": "update_health",
        "description": "Update health metrics, energy levels, mental health, goals, and current state",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "data": {"type": "OBJECT", "description": "Health data to update"}
            },
            "required": ["data"]
        }
    },
    {
        "name": "update_tech_inventory",
        "description": "Update tech inventory (hardware, software, wishlist)",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "data": {"type": "OBJECT", "description": "Tech inventory data to update"}
            },
            "required": ["data"]
        }
    },
    {
        "name": "update_active_projects",
        "description": "Update active projects and tasks",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "data": {"type": "OBJECT", "description": "Project data to update"}
            },
            "required": ["data"]
        }
    },
    {
        "name": "update_routines",
        "description": "Update weekly routines and templates",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "data": {"type": "OBJECT", "description": "Routines data to update"}
            },
            "required": ["data"]
        }
    },
    {
        "name": "update_pantry_staples",
        "description": "Update pantry inventory",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "data": {"type": "OBJECT", "description": "Pantry data to update"}
            },
            "required": ["data"]
        }
    },
    {
        "name": "update_meal_rotation",
        "description": "Update meal rotation and recipes",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "data": {"type": "OBJECT", "description": "Meal data to update"}
            },
            "required": ["data"]
        }
    },
    {
        "name": "update_finance",
        "description": "Update financial data (budget, subscriptions)",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "data": {"type": "OBJECT", "description": "Finance data to update"}
            },
            "required": ["data"]
        }
    },
    {
        "name": "create_data_file",
        "description": "Create a new JSON data file for a new category",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "filename": {"type": "STRING", "description": "Name of the file (e.g., 'books.json')"},
                "initial_data": {"type": "OBJECT", "description": "Initial data structure"},
                "description": {"type": "STRING", "description": "Description of the file's purpose"}
            },
            "required": ["filename", "initial_data"]
        }
    },
    {
        "name": "update_data_file",
        "description": "Update any generic data file",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "filename": {"type": "STRING", "description": "Name of the file to update"},
                "data": {"type": "OBJECT", "description": "Data to merge into the file"}
            },
            "required": ["filename", "data"]
        }
    },
    {
        "name": "list_data_files",
        "description": "List all available data files to check what categories exist",
        "parameters": {
            "type": "OBJECT",
            "properties": {},
            "required": []
        }
    }
]

