from functools import wraps
from flask import request, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.users.models import User
import hmac

def role_required(roles):
    """Decorator to ensure user has one of the specified roles."""
    if not isinstance(roles, list):
        roles = [roles]

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            
            # Convert user_id to int if it's a string
            if isinstance(user_id, str):
                try:
                    user_id = int(user_id)
                except ValueError:
                    raise UnauthorizedError("Invalid user identity")
            
            # Store user_id in g for audit logging
            g.user_id = user_id
                    
            current_user = User.query.get(user_id)
            if not current_user:
                raise UnauthorizedError("User not found")
                
            if not current_user.is_active:
                raise ForbiddenError("Account is inactive")
                
            if not current_user.role or current_user.role.name not in roles:
                raise ForbiddenError("Insufficient permissions")
                
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def admin_required(fn):
    """Decorator to ensure user has the 'Admin' role."""
    return role_required(['Admin'])(fn)


def api_key_required(fn):
    """Decorator to protect endpoints with API key authentication."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        if not api_key:
            return {"message": "Missing API Key"}, 401
            
        # Retrieve server API keys from app config
        server_api_keys = current_app.config.get('SERVER_API_KEYS', {})
        
        # More secure constant-time comparison to prevent timing attacks
        is_valid_key = False
        for key_name, stored_key in server_api_keys.items():
            if hmac.compare_digest(api_key, stored_key):
                is_valid_key = True
                break
                
        if not is_valid_key:
            return {"message": "Invalid API Key"}, 401
            
        return fn(*args, **kwargs)
    return wrapper