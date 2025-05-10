from functools import wraps
from flask import request, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.users.models import User # Assuming User model is in app.users.models

def role_required(roles):
    """Decorator to ensure user has one of the specified roles."""
    if not isinstance(roles, list):
        roles = [roles]

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            current_user = User.query.get(user_id)
            if not current_user or not current_user.role or current_user.role.name not in roles:
                return {"message": "Insufficient permissions"}, 403
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
        # Retrieve server API keys from app config (loaded from env or Secret Manager)
        # Example: current_app.config['SERVER_API_KEYS'] = {'service_a': 'key_a', 'service_b': 'key_b'}
        server_api_keys = current_app.config.get('SERVER_API_KEYS', {})
        
        if not api_key or api_key not in server_api_keys.values():
            # More robust check: compare api_key against a list of valid, hashed API keys
            # For now, simple check if key exists as one of the configured values
            return {"message": "Invalid or missing API Key"}, 401 # 401 Unauthorized or 403 Forbidden
        return fn(*args, **kwargs)
    return wrapper

# Placeholder for future: Permission-based decorator
# def permission_required(permission_name):
#     def decorator(fn):
#         @wraps(fn)
#         def wrapper(*args, **kwargs):
#             verify_jwt_in_request()
#             user_id = get_jwt_identity()
#             current_user = User.query.get(user_id)
#             if not current_user or not current_user.has_permission(permission_name): # Assumes has_permission method on User model
#                 return {"message": "Insufficient permissions for this action"}, 403
#             return fn(*args, **kwargs)
#         return wrapper
#     return decorator
