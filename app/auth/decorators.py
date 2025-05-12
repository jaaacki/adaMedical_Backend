# app/auth/decorators.py
from functools import wraps
from flask import request, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.users.models import User # Using the new users module path

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
                    return {"message": "Invalid user identity"}, 401
                    
            current_user = User.query.get(user_id)
            
            # Check if user exists and has a role
            if not current_user or not current_user.role:
                return {"message": "Insufficient permissions"}, 403
                
            # Check if user's role name matches any of the required roles
            # Also match variations to handle typos (e.g., "Admininstrator" for "Administrator")
            user_role_name = current_user.role.name.lower()
            
            # Check for exact match first
            if any(role.lower() == user_role_name for role in roles):
                return fn(*args, **kwargs)
                
            # Additional check for "admin" variants with typos
            if 'admin' in [r.lower() for r in roles]:
                # Check for common misspellings or variants of "admin"
                admin_variants = ['admin', 'administrator', 'admininstrator']
                if any(variant in user_role_name for variant in admin_variants):
                    return fn(*args, **kwargs)
            
            return {"message": "Insufficient permissions"}, 403
        return wrapper
    return decorator

def admin_required(fn):
    """Decorator to ensure user has the 'Admin' role or any recognized variant."""
    return role_required(['Admin'])(fn)