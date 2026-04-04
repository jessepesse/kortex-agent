"""
Config routes - API keys, models, settings
"""

import os
import logging

from flask import request

from kortex import config
from backend.errors import handle_exceptions, ValidationError, success_response

logger = logging.getLogger(__name__)


def register_config_routes(app):
    """Register configuration endpoints"""
    
    @app.route('/api/config', methods=['GET'])
    @handle_exceptions
    def get_config():
        """Get current configuration including available models"""
        cfg = config.load_config()
        return success_response(data={
            "providers": cfg.get("models", {}),
            "default_provider": cfg.get("default_provider", "google"),
            "default_model": cfg.get("default_model", "gemini-3-flash-preview"),
        })

    @app.route('/api/models', methods=['GET'])
    @handle_exceptions
    def get_models():
        """Get available models and current selection"""
        cfg = config.load_config()
        return success_response(data={
            "providers": cfg['models'],
            "current_provider": cfg['default_provider'],
            "current_model": cfg['default_model']
        })
    
    @app.route('/api/models', methods=['POST'])
    @handle_exceptions
    def set_model():
        """Set the default model and provider"""
        req_data = request.get_json()
        provider = req_data.get('provider')
        model = req_data.get('model')
        
        if not provider or not model:
            raise ValidationError("Provider and model are required")
        
        cfg = config.load_config()
        
        if provider not in cfg['models']:
            raise ValidationError(f"Invalid provider: {provider}")

        # Ollama models are dynamic — skip static model validation
        if provider != "ollama":
            # Check if model exists in provider's model list (now objects with 'id' field)
            model_ids = [m['id'] if isinstance(m, dict) else m for m in cfg['models'][provider]]
            if model not in model_ids:
                raise ValidationError(f"Invalid model: {model}")
        
        cfg['default_provider'] = provider
        cfg['default_model'] = model
        config.save_config(cfg)
        
        return success_response(message=f"Switched to {provider}: {model}")

    @app.route('/api/config/api-keys', methods=['GET'])
    @handle_exceptions
    def get_api_keys_status():
        """Check which API keys are configured (without revealing the keys)"""
        cfg = config.load_config()
        return success_response(data={
            "openai": bool(cfg['api_keys'].get('openai')),
            "google": bool(cfg['api_keys'].get('google'))
        })
    
    @app.route('/api/config/api-keys', methods=['POST'])
    @handle_exceptions
    def set_api_keys():
        """Set API keys"""
        req_data = request.get_json()
        cfg = config.load_config()
        
        if 'openai' in req_data and req_data['openai']:
            cfg['api_keys']['openai'] = req_data['openai']
        
        if 'google' in req_data and req_data['google']:
            cfg['api_keys']['google'] = req_data['google']
        
        config.save_config(cfg)
        return success_response(message="API keys updated")

    @app.route('/api/ollama/models', methods=['GET'])
    @handle_exceptions
    def get_ollama_models():
        """Fetch available models from local Ollama instance"""
        import requests as http_requests

        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        try:
            resp = http_requests.get(f"{base_url}/api/tags", timeout=3)
            resp.raise_for_status()
            models_data = resp.json()

            models = []
            for m in models_data.get("models", []):
                name = m.get("name", "")
                # Strip ":latest" suffix for cleaner display
                display_name = name.replace(":latest", "") if name.endswith(":latest") else name
                size_gb = round(m.get("size", 0) / (1024**3), 1)
                models.append({
                    "id": name,
                    "display_name": display_name,
                    "size_gb": size_gb,
                    "family": m.get("details", {}).get("family", ""),
                    "parameter_size": m.get("details", {}).get("parameter_size", ""),
                })

            return success_response(data={
                "available": True,
                "models": models,
                "base_url": base_url
            })
        except http_requests.ConnectionError:
            return success_response(data={
                "available": False,
                "models": [],
                "error": "Ollama not detected — is it installed and running?"
            })
        except Exception as e:
            logger.warning("Ollama model fetch failed: %s", e)
            return success_response(data={
                "available": False,
                "models": [],
                "error": f"Failed to connect to Ollama: {str(e)}"
            })
