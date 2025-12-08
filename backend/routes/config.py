"""
Config routes - API keys, models, settings
"""

from flask import request, jsonify

from kortex import config
from backend.errors import handle_exceptions, ValidationError, success_response


def register_config_routes(app):
    """Register configuration endpoints"""
    
    @app.route('/api/config', methods=['GET'])
    @handle_exceptions
    def get_config():
        """Get current configuration including available models"""
        cfg = config.load_config()
        return jsonify({
            'providers': cfg.get('models', {}),
            'default_provider': cfg.get('default_provider', 'google'),
            'default_model': cfg.get('default_model', 'gemini-2.5-flash')
        })

    @app.route('/api/models', methods=['GET'])
    @handle_exceptions
    def get_models():
        """Get available models and current selection"""
        cfg = config.load_config()
        return jsonify({
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
        
        if model not in cfg['models'][provider]:
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
        return jsonify({
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
