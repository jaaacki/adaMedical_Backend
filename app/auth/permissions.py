from functools import wraps
from flask import g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.users.models import User
from app.core.errors import ForbiddenError, UnauthorizedError

class Permission:
    """Define permission constants."""
    
    # Resource-specific permissions
    VIEW_USERS = 'users.view'
    EDIT_USERS = 'users.edit'
    CREATE_USERS = 'users.create'
    DELETE_USERS = 'users.delete'
    
    # Define patterns for future modules
    VIEW_PRODUCTS = 'products.view'
    EDIT_PRODUCTS = 'products.edit'
    CREATE_PRODUCTS = 'products.create'
    DELETE_PRODUCTS = 'products.delete'
    
    # More permissions will be added for other modules
    
    # Role-based permission sets
    ROLE_PERMISSIONS = {
        'Admin': [
            # Admin can do everything
            'users.*', 'products.*', 'inventory.*', 'orders.*', 
            'invoices.*', 'contacts.*', 'organizations.*'
        ],
        'Sales': [
            # Sales can view everything, manage orders and contacts
            '*.view', 'orders.*', 'contacts.*', 'organizations.*'
        ],
        'Operations': [
            # Operations manages inventory and delivery
            '*.view', 'inventory.*', 'products.view', 'orders.view', 'orders.edit'
        ],
        'Accounts': [
            # Accounts manages invoices and payments
            '*.view', 'invoices.*', 'payments.*'
        ]
    }
    
    @staticmethod
    def expand_permissions(permission_patterns):
        """Expand permission patterns like '*.view' to individual permissions."""
        all_permissions = [
            f'{resource}.{action}' for resource in 
            ['users', 'products', 'inventory', 'orders', 'invoices', 'contacts', 'organizations', 'payments']
            for action in ['view', 'edit', 'create', 'delete']
        ]
        
        expanded = set()
        for pattern in permission_patterns:
            if pattern == '*.*':
                # All permissions
                expanded.update(all_permissions)
            elif pattern.endswith('.*'):
                # All actions for a resource
                resource = pattern.split('.')[0]
                expanded.update([p for p in all_permissions if p.startswith(f'{resource}.')])
            elif pattern.startswith('*.'):
                # One action for all resources
                action = pattern.split('.')[1]
                expanded.update([p for p in all_permissions if p.endswith(f'.{action}')])
            else:
                # Specific permission
                expanded.add(pattern)
        
        return expanded

    @classmethod
    def get_role_permissions(cls, role_name):
        """Get permissions for a role."""
        if role_name not in cls.ROLE_PERMISSIONS:
            return set()
        
        return cls.expand_permissions(cls.ROLE_PERMISSIONS[role_name])

def permission_required(permission):
    """Decorator to check for a permission."""
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
                
            if not current_user.role:
                raise ForbiddenError("User has no assigned role")
            
            # Special case for Admin role - admin can do everything
            if current_user.role.name == 'Admin':
                return fn(*args, **kwargs)
            
            # Get permissions for the user's role
            user_permissions = Permission.get_role_permissions(current_user.role.name)
            
            # Check if user has the required permission
            if permission not in user_permissions:
                raise ForbiddenError(f"Missing required permission: {permission}")
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator