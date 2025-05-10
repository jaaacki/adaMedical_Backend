from flask import current_app, redirect, url_for, request # Removed session as it's implicitly handled by Authlib state, jsonify not needed
from flask_restx import Namespace, Resource # Removed fields as token_model_output is imported
from flask_jwt_extended import create_access_token, create_refresh_token

from app.extensions import db, oauth # Import initialized extensions
from app.users.models import User, Role
# For serializing user info, token_model_output for Swagger
from app.users.routes import token_model_output 

ns = Namespace('auth', description='Authentication operations including Google SSO')

# For Swagger: Define expected callback query parameters (though handled by Authlib)
google_callback_params = ns.parser()
google_callback_params.add_argument('code', type=str, required=True, help='Authorization code from Google')
google_callback_params.add_argument('state', type=str, required=True, help='State parameter for CSRF protection')


def get_or_create_default_role(role_name_config_key='DEFAULT_USER_ROLE', default_rolename='User'):
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

@ns.route('/google/login')
class GoogleLogin(Resource):
    @ns.doc(description='Initiates Google OAuth2 login flow. Redirects to Google.')
    def get(self):
        """Redirect to Google to authorize the application."""
        if not current_app.config.get('GOOGLE_CLIENT_ID') or \
           not current_app.config.get('GOOGLE_CLIENT_SECRET') or \
           not current_app.config.get('GOOGLE_REDIRECT_URI'): # Check redirect URI also
            current_app.logger.error("Google SSO not configured completely on the server (ID, Secret, or Redirect URI missing).")
            return {"message": "Google SSO not configured correctly on the server."}, 500
        
        redirect_uri = url_for('api.v1_auth_google_callback', _external=True)
        current_app.logger.debug(f"Using Google redirect URI: {redirect_uri} from url_for based on GOOGLE_REDIRECT_URI: {current_app.config.get('GOOGLE_REDIRECT_URI')}")
        
        if 'google' not in oauth._clients:
             current_app.logger.error("OAuth 'google' client not registered. Check app initialization.")
             return {"message": "OAuth client not registered. Check server configuration."}, 500

        # Authlib handles session/state for CSRF protection internally
        return oauth.google.authorize_redirect(redirect_uri)

@ns.route('/google/callback')
class GoogleCallback(Resource):
    @ns.doc(description='Handles the callback from Google after authentication. Issues JWT tokens on success.',
              params=google_callback_params.args) # Corrected to pass args
    @ns.marshal_with(token_model_output) 
    @ns.response(401, 'Authentication failed')
    @ns.response(500, 'SSO Configuration error or internal error')
    def get(self):
        """Process Google OAuth callback, create/login user, and return JWT tokens."""
        try:
            token = oauth.google.authorize_access_token()
        except Exception as e:
            current_app.logger.error(f"Error authorizing Google access token: {e}", exc_info=True)
            return {"message": f"Google authentication failed: {str(e)}"}, 401

        if not token or 'userinfo' not in token:
            current_app.logger.error("Failed to fetch userinfo from Google token or token is invalid.")
            return {"message": "Could not fetch user information from Google."}, 401

        user_info = oauth.google.parse_id_token(token) if 'id_token' in token else token.get('userinfo')
        if not user_info:
            current_app.logger.error("Userinfo is empty after parsing Google token.")
            return {"message": "Could not parse user information from Google token."}, 401

        google_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name', email.split('@')[0] if email else 'User')
        # profile_pic = user_info.get('picture') # Optional

        if not email:
            current_app.logger.error("Email not provided by Google. Cannot process login.")
            return {"message": "Email not provided by Google. Cannot process login."}, 400

        user = User.query.filter_by(email=email).first() # Prioritize email for existing accounts

        if not user:
            # If no user by email, check if there's one by google_sso_id (e.g. email changed in Google)
            if google_id:
                user = User.query.filter_by(google_sso_id=google_id).first()

            if not user: # Still no user, create new one
                user = User(
                    email=email,
                    name=name,
                    google_sso_id=google_id,
                    is_active=True,
                    currency_context=current_app.config.get('DEFAULT_CURRENCY', 'SGD')
                )
                default_role = get_or_create_default_role()
                if default_role:
                    user.role = default_role
                else:
                    current_app.logger.error(f"User {email} created via SSO could not be assigned a default role.")
                
                db.session.add(user)
                try:
                    db.session.commit()
                    current_app.logger.info(f"New user {email} created via Google SSO and committed.")
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"Error creating new SSO user {email}: {e}", exc_info=True)
                    return {"message": "Error creating new user account."}, 500
            else: # User found by google_sso_id, potential email update
                if user.email != email:
                    current_app.logger.info(f"User {user.email} (ID: {user.id}) SSO email changed to {email}. Updating.")
                    user.email = email # Update email if it changed in Google for existing SSO user
                # Fall through to common user update logic below

        # Common logic for existing or newly created user from SSO path
        updated_fields = False
        if not user.google_sso_id and google_id:
            user.google_sso_id = google_id
            updated_fields = True
        if not user.is_active:
            user.is_active = True # Re-activate if they login via SSO
            updated_fields = True
        
        if updated_fields:
            try:
                db.session.commit()
                current_app.logger.info(f"User {email} (ID: {user.id}) updated and committed (SSO link/activation).")
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error updating SSO user {email}: {e}", exc_info=True)
                return {"message": "Error updating user account during SSO login."}, 500

        if not user.is_active:
             current_app.logger.warning(f"SSO login attempt for inactive user {email} (ID: {user.id}). Denying access.")
             return {"message": "User account is inactive. Please contact support."}, 403

        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        current_app.logger.info(f"User {email} (ID: {user.id}) successfully logged in via Google SSO.")
        return {'access_token': access_token, 'refresh_token': refresh_token}, 200

def register_oauth_client(app_oauth, app_config):
    """Helper to register OAuth clients. Called from create_app."""
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
