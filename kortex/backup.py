"""Backup and restore functionality for Kortex Agent"""

from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, List, Dict

from .config import DATA_DIR, CONFIG_FILE
from .data import get_conversations_dir, list_conversations, validate_filename, validate_chat_id, build_safe_conv_path


def create_backup(conversation_ids: Optional[List[str]] = None) -> bytes:
    """
    Create a ZIP backup of all data.
    
    Args:
        conversation_ids: List of conversation IDs to include. 
                         None means include all, empty list means none.
    
    Returns:
        ZIP file as bytes
    """
    buffer = io.BytesIO()
    
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        data_files = []
        conversation_files = []
        
        # 1. Add all data/*.json files (except conversations folder)
        if DATA_DIR.exists():
            for json_file in DATA_DIR.glob("*.json"):
                relative_path = f"data/{json_file.name}"
                zf.write(json_file, relative_path)
                data_files.append(json_file.name)
        
        # 2. Add selected conversations
        conv_dir = get_conversations_dir()
        if conv_dir.exists():
            if conversation_ids is None:
                # Include all conversations
                for conv_file in conv_dir.glob("*.json"):
                    relative_path = f"conversations/{conv_file.name}"
                    zf.write(conv_file, relative_path)
                    conversation_files.append(conv_file.name)
            elif conversation_ids:
                # Include only selected conversations
                for conv_id in conversation_ids:
                    try:
                        # CodeQL: ID is validated before use in path construction
                        conv_id = validate_chat_id(conv_id)
                    except ValueError:
                        continue
                        
                    conv_file = conv_dir / f"{conv_id}.json"
                    if conv_file.exists():
                        relative_path = f"conversations/{conv_file.name}"
                        zf.write(conv_file, relative_path)
                        conversation_files.append(conv_file.name)
        
        # 3. Add config.json
        config_included = False
        if CONFIG_FILE.exists():
            zf.write(CONFIG_FILE, "config.json")
            config_included = True
        
        # 4. Create and add manifest
        manifest = {
            "version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "kortex_version": "1.0.0-alpha7",
            "files": {
                "data": sorted(data_files),
                "conversations": sorted(conversation_files),
                "config": config_included
            },
            "stats": {
                "data_files": len(data_files),
                "conversations": len(conversation_files),
                "total_files": len(data_files) + len(conversation_files) + (1 if config_included else 0)
            }
        }
        
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
    
    buffer.seek(0)
    return buffer.getvalue()


def validate_backup(zip_bytes: bytes) -> Dict[str, Any]:
    """
    Validate a backup file.
    
    Returns:
        {
            "valid": bool,
            "errors": list[str],
            "warnings": list[str],
            "manifest": dict or None,
            "files": list[str]
        }
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "manifest": None,
        "files": []
    }
    
    # 1. Check if valid ZIP
    try:
        buffer = io.BytesIO(zip_bytes)
        with zipfile.ZipFile(buffer, 'r') as zf:
            result["files"] = zf.namelist()
            
            # 2. Check manifest exists
            if "manifest.json" not in result["files"]:
                result["errors"].append("Backup-manifest puuttuu (manifest.json)")
                result["valid"] = False
            else:
                # Parse manifest
                try:
                    manifest_content = zf.read("manifest.json")
                    result["manifest"] = json.loads(manifest_content)
                    
                    # Check version compatibility
                    version = result["manifest"].get("version", "0")
                    if version not in ["1.0"]:
                        result["warnings"].append(f"Tuntematon backup-versio: {version}")
                        
                except json.JSONDecodeError:
                    result["errors"].append("Manifest.json ei ole validi JSON")
                    result["valid"] = False
            
            # 3. Validate each JSON file
            for filename in result["files"]:
                if filename.endswith(".json"):
                    try:
                        content = zf.read(filename)
                        json.loads(content)
                    except json.JSONDecodeError:
                        result["errors"].append(f"Virheellinen JSON: {filename}")
                        result["valid"] = False
            
            # 4. Check for data files
            data_files = [f for f in result["files"] if f.startswith("data/")]
            if not data_files:
                result["warnings"].append("Backup ei sisällä data-tiedostoja")
                
    except zipfile.BadZipFile:
        result["errors"].append("Tiedosto ei ole validi ZIP-arkisto")
        result["valid"] = False
    except Exception as e:
        result["errors"].append(f"Virhe käsittelyssä: {str(e)}")
        result["valid"] = False
    
    return result


def restore_backup(zip_bytes: bytes) -> Dict[str, Any]:
    """
    Restore from a backup. OVERWRITES ALL DATA!
    
    Returns:
        {
            "success": bool,
            "restored_files": list[str],
            "errors": list[str]
        }
    """
    result = {
        "success": True,
        "restored_files": [],
        "errors": []
    }
    
    # 1. Validate first
    validation = validate_backup(zip_bytes)
    if not validation["valid"]:
        result["success"] = False
        result["errors"] = validation["errors"]
        return result
    
    try:
        buffer = io.BytesIO(zip_bytes)
        with zipfile.ZipFile(buffer, 'r') as zf:
            
            # 2. Restore data files
            for filename in zf.namelist():
                if filename.startswith("data/") and filename.endswith(".json"):
                    # Extract to DATA_DIR
                    target_name = filename.replace("data/", "")
                    
                    try:
                        # Validate path to prevent Zip Slip
                        target_path = validate_filename(target_name)
                        
                        content = zf.read(filename)
                        # Validate JSON before writing
                        json.loads(content)
                        
                        DATA_DIR.mkdir(parents=True, exist_ok=True)
                        with open(target_path, 'wb') as f:
                            f.write(content)
                        result["restored_files"].append(f"data/{target_name}")
                    except Exception as e:
                        result["errors"].append(f"Virhe palautettaessa {filename}: {str(e)}")
                
                elif filename.startswith("conversations/") and filename.endswith(".json"):
                    # Extract to conversations dir
                    target_name = filename.replace("conversations/", "").replace(".json", "")
                    
                    try:
                        # Validate ID and use safe path builder
                        safe_id = validate_chat_id(target_name)
                        target_path = build_safe_conv_path(safe_id)
                        
                        content = zf.read(filename)
                        json.loads(content)
                        
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(target_path, 'wb') as f:  # lgtm[py/path-injection]
                            f.write(content)
                        result["restored_files"].append(f"conversations/{safe_id}.json")
                    except Exception:
                        result["errors"].append("Error restoring conversation file")
                
                elif filename == "config.json":
                    # Restore config
                    try:
                        content = zf.read(filename)
                        json.loads(content)
                        
                        with open(CONFIG_FILE, 'wb') as f:
                            f.write(content)
                        result["restored_files"].append("config.json")
                    except Exception as e:
                        result["errors"].append(f"Virhe palautettaessa config.json: {str(e)}")
            
            if result["errors"]:
                result["success"] = False
                
    except Exception as e:
        result["success"] = False
        result["errors"].append(f"Virhe palautuksessa: {str(e)}")
    
    return result


def get_backup_filename() -> str:
    """Generate a backup filename with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    return f"kortex_backup_{timestamp}.zip"
