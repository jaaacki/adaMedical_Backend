from app.core.repository import BaseRepository
from app.users.models import User, Role
from app.extensions import db

class UserRepository(BaseRepository):
    """Repository for User model operations."""
    
    model_class = User
    
    def get_by_email(self, email):
        """Get a user by email."""
        return User.query.filter_by(email=email).first()
    
    def get_by_google_sso_id(self, google_sso_id):
        """Get a user by Google SSO ID."""
        return User.query.filter_by(google_sso_id=google_sso_id).first()
    
    def get_with_role(self, user_id):
        """Get a user with role data eagerly loaded."""
        return User.query.options(
            db.joinedload(User.role)
        ).filter_by(id=user_id).first()

class RoleRepository(BaseRepository):
    """Repository for Role model operations."""
    
    model_class = Role
    
    def get_by_name(self, name):
        """Get a role by name."""
        return Role.query.filter_by(name=name).first()
    
    def get_default_role(self):
        """Get the default role for new users."""
        from flask import current_app
        default_role_name = current_app.config.get('DEFAULT_USER_ROLE', 'User')
        return self.get_by_name(default_role_name)