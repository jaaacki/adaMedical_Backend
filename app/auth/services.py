from flask import current_app, url_for
from app.users.services import UserService
from app.users.models import User, Role
from app.extensions import db, oauth
from app.core.errors import NotFoundError, BadRequestError, ForbiddenError

class AuthService:
    """Service for authentication operations."""
    
    def __init__(self):
        self.user_service = UserService()
    
    def get_or_create_default_role(self, role_name_config_key='DEFAULT_USER_ROLE', default_rolename='User'):
        """Gets or creates a role, typically the default role for new users."""
        rolename = current_app.config.get(role_name_config_key, default_rolename)
        role = Role.query.filter_by(name=rolename).first()
        if not role:
            current_app.logger.info(f"Default role '{rolename}' not found. Creating it.")
            role = Role(name=rolename)
            db.session.add(role)
            try:
                db.session.commit()
                current_app.logger.info(f"Created default role '{rolename}'.")
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Could not create role '{rolename}': {e}")
                return None # Indicate failure
        return role
    
    def process_google_auth(self, token):
        """Process Google OAuth token and create/update user."""
        if not token or 'userinfo' not in token:
            raise BadRequestError("Invalid or missing token data")
        
        # Extract user info from token
        user_info = oauth.google.parse_id_token(token) if 'id_token' in token else token.get('userinfo')
        if not user_info:
            raise BadRequestError("Could not parse user information from Google token")
        
        google_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name', email.split('@')[0] if email else 'User')
        
        if not email:
            raise BadRequestError("Email not provided by Google. Cannot process login.")
        
        # Try to find existing user by email first, then by Google SSO ID
        user = self.user_service.get_user_by_email(email)
        
        if not user and google_id:
            # Check if there's a user with this Google ID but different email
            user = User.query.filter_by(google_sso_id=google_id).first()
        
        if not user:
            # Create new user for SSO login
            user = self._create_sso_user(email, name, google_id)
        else:
            # Update existing user with SSO data if needed
            user = self._update_user_sso_data(user, email, google_id)
        
        if not user.is_active:
            raise ForbiddenError("User account is inactive. Please contact support.")
        
        return user
    
    def _create_sso_user(self, email, name, google_id):
        """Create a new user from SSO data."""
        # Get default role
        default_role = self.get_or_create_default_role()
        if not default_role:
            current_app.logger.error(f"Could not assign default role to new SSO user {email}")
        
        # Create user
        user = User(
            email=email,
            name=name,
            google_sso_id=google_id,
            is_active=True,
            currency_context=current_app.config.get('DEFAULT_CURRENCY', 'SGD')
        )
        
        if default_role:
            user.role = default_role
        
        db.session.add(user)
        try:
            db.session.commit()
            current_app.logger.info(f"New user {email} created via Google SSO.")
            return user
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating new SSO user {email}: {e}")
            raise
    
    def _update_user_sso_data(self, user, email, google_id):
        """Update existing user with SSO data if needed."""
        updated = False
        
        # Update email if changed in Google (for existing SSO users)
        if user.google_sso_id and user.email != email:
            current_app.logger.info(f"User {user.email} (ID: {user.id}) SSO email changed to {email}. Updating.")
            user.email = email
            updated = True
        
        # Link with Google if not already linked
        if not user.google_sso_id and google_id:
            user.google_sso_id = google_id
            updated = True
        
        # Activate account if inactive
        if not user.is_active:
            user.is_active = True
            updated = True
        
        if updated:
            try:
                db.session.commit()
                current_app.logger.info(f"User {email} (ID: {user.id}) updated during SSO login.")
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error updating SSO user {email}: {e}")
                raise
        
        return user

def register_oauth_client(app_oauth, app_config):
    """Helper to register OAuth clients."""
    google_client_id = app_config.get('GOOGLE_CLIENT_ID')
    google_client_secret = app_config.get('GOOGLE_CLIENT_SECRET')
    google_discovery_url = app_config.get('GOOGLE_DISCOVERY_URL')
    google_scopes = app_config.get('GOOGLE_OAUTH_SCOPES')

    if google_client_id and google_client_secret and google_discovery_url and google_scopes:
        app_oauth.register(
            name='google',
            client_id=google_client_id,
            client_secret=google_client_secret,
            server_metadata_url=google_discovery_url,
            client_kwargs={
                'scope': ' '.join(google_scopes)
            }
        )
        current_app.logger.info("Google OAuth client registered successfully.")
    else:
        missing_configs = []
        if not google_client_id: missing_configs.append('GOOGLE_CLIENT_ID')
        if not google_client_secret: missing_configs.append('GOOGLE_CLIENT_SECRET')
        if not google_discovery_url: missing_configs.append('GOOGLE_DISCOVERY_URL')
        if not google_scopes: missing_configs.append('GOOGLE_OAUTH_SCOPES')
        current_app.logger.warning(f"Google OAuth client NOT registered. Missing configurations: {', '.join(missing_configs)}.")
