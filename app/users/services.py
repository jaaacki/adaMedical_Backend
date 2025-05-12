from app.users.repositories import UserRepository, RoleRepository
from app.users.models import User, Role
from app.extensions import db
from app.core.errors import NotFoundError, ConflictError, BadRequestError, ForbiddenError
from flask import current_app

class UserService:
    """Service layer for user operations."""
    
    def __init__(self):
        self.user_repo = UserRepository()
        self.role_repo = RoleRepository()
    
    def get_user_by_id(self, user_id):
        """Get user by ID."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")
        return user
    
    def get_user_by_email(self, email):
        """Get user by email."""
        return self.user_repo.get_by_email(email)
    
    def list_users(self, **filters):
        """List users with optional filters."""
        return self.user_repo.list(**filters)
    
    def create_user(self, data):
        """Create a new user."""
        if self.get_user_by_email(data['email']):
            raise ConflictError(f"User with email {data['email']} already exists")
        
        user = User(
            name=data['name'],
            email=data['email'],
            is_active=data.get('is_active', True),
            currency_context=data.get('currency_context', current_app.config.get('DEFAULT_CURRENCY', 'SGD'))
        )
        
        if 'password' in data:
            user.set_password(data['password'])
        
        if 'role_id' in data and data['role_id']:
            role = self.role_repo.get_by_id(data['role_id'])
            if not role:
                raise NotFoundError(f"Role with ID {data['role_id']} not found")
            user.role = role
        
        try:
            db.session.add(user)
            db.session.commit()
            return user
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating user: {e}")
            raise
    
    def update_user(self, user_id, data):
        """Update a user."""
        user = self.get_user_by_id(user_id)
        
        if 'name' in data:
            user.name = data['name']
        
        if 'email' in data and data['email'] != user.email:
            existing_user = self.get_user_by_email(data['email'])
            if existing_user and existing_user.id != user_id:
                raise ConflictError(f"Email {data['email']} is already in use")
            user.email = data['email']
        
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        if 'currency_context' in data:
            user.currency_context = data['currency_context']
        
        if 'role_id' in data:
            if data['role_id'] is None:
                user.role_id = None
            else:
                role = self.role_repo.get_by_id(data['role_id'])
                if not role:
                    raise NotFoundError(f"Role with ID {data['role_id']} not found")
                user.role_id = role.id
        
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        try:
            db.session.commit()
            return user
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating user: {e}")
            raise
    
    def update_user_profile(self, user_id, data):
        """Update a user's own profile."""
        user = self.get_user_by_id(user_id)
        
        if 'name' in data:
            user.name = data['name']
        
        if 'currency_context' in data:
            user.currency_context = data['currency_context']
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if new_password:
            if user.google_sso_id and not user.password_hash:
                # SSO users with no password can't set one
                raise ForbiddenError("Password management is not available for accounts linked with Google SSO")
            
            if user.password_hash and not current_password:
                # Need current password to change password
                raise BadRequestError("Current password is required to set a new password")
            
            if user.password_hash and not user.check_password(current_password):
                raise BadRequestError("Incorrect current password")
            
            user.set_password(new_password)
        
        try:
            db.session.commit()
            return user
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating user profile: {e}")
            raise
    
    def delete_user(self, user_id):
        """Delete a user."""
        user = self.get_user_by_id(user_id)
        
        try:
            db.session.delete(user)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting user: {e}")
            raise
    
    def authenticate_user(self, email, password):
        """Authenticate a user with email and password."""
        user = self.get_user_by_email(email)
        
        if not user or not user.password_hash or not user.check_password(password):
            return None
        
        if not user.is_active:
            raise ForbiddenError("User account is inactive")
        
        return user

class RoleService:
    """Service layer for role operations."""
    
    def __init__(self):
        self.role_repo = RoleRepository()
    
    def get_role_by_id(self, role_id):
        """Get role by ID."""
        role = self.role_repo.get_by_id(role_id)
        if not role:
            raise NotFoundError(f"Role with ID {role_id} not found")
        return role
    
    def get_role_by_name(self, name):
        """Get role by name."""
        return self.role_repo.get_by_name(name)
    
    def list_roles(self):
        """List all roles."""
        return self.role_repo.list()
    
    def create_role(self, data):
        """Create a new role."""
        if self.get_role_by_name(data['name']):
            raise ConflictError(f"Role with name {data['name']} already exists")
        
        role = Role(name=data['name'])
        
        try:
            db.session.add(role)
            db.session.commit()
            return role
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating role: {e}")
            raise
    
    def update_role(self, role_id, data):
        """Update a role."""
        role = self.get_role_by_id(role_id)
        
        if 'name' in data and data['name'] != role.name:
            existing_role = self.get_role_by_name(data['name'])
            if existing_role:
                raise ConflictError(f"Role name {data['name']} is already in use")
            role.name = data['name']
        
        try:
            db.session.commit()
            return role
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating role: {e}")
            raise
    
    def delete_role(self, role_id):
        """Delete a role."""
        role = self.get_role_by_id(role_id)
        
        # Check core roles
        if role.name.lower() == 'admin':
            raise ForbiddenError("Cannot delete the core 'Admin' role")
        
        from flask import current_app
        if role.name.lower() == current_app.config.get('DEFAULT_USER_ROLE', 'User').lower():
            raise ForbiddenError(f"Cannot delete the default system role '{role.name}'")
        
        # Check if role is in use
        if role.users.first():
            raise BadRequestError(f"Cannot delete role '{role.name}', it is currently assigned to users")
        
        try:
            db.session.delete(role)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting role: {e}")
            raise