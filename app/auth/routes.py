from flask import current_app, redirect, url_for, request, jsonify
from flask_restx import Namespace, Resource
from flask_jwt_extended import create_access_token, create_refresh_token

from app.extensions import db, oauth
from app.users.models import User
from app.users.routes import token_model_output 
from app.auth.services import AuthService
from app.core.errors import BadRequestError, ForbiddenError, UnauthorizedError

# Create service instance
auth_service = AuthService()

ns = Namespace('auth', description='Authentication operations including Google SSO')

# For Swagger: Define expected callback query parameters
google_callback_params = ns.parser()
google_callback_params.add_argument('code', type=str, required=True, help='Authorization code from Google')
google_callback_params.add_argument('state', type=str, required=True, help='State parameter for CSRF protection')

@ns.route('/google/callback')
class GoogleCallback(Resource):
    @ns.doc(description='Handles the callback from Google after authentication. Issues JWT tokens on success.')
    @ns.expect(google_callback_params)
    @ns.marshal_with(token_model_output) 
    @ns.response(401, 'Authentication failed')
    @ns.response(500, 'SSO Configuration error or internal error')
    def get(self):
        """Process Google OAuth callback, create/login user, and return JWT tokens."""
        try:
            # Try to obtain the access token
            token = oauth.google.authorize_access_token()
            
            # Validate we have the userinfo
            if not token or 'userinfo' not in token:
                current_app.logger.error("Failed to fetch userinfo from Google token or token is invalid.")
                return {"message": "Could not fetch user information from Google."}, 401

            # Parse user info from token
            user_info = oauth.google.parse_id_token(token) if 'id_token' in token else token.get('userinfo')
            if not user_info:
                current_app.logger.error("Userinfo is empty after parsing Google token.")
                return {"message": "Could not parse user information from Google token."}, 401

            # Extract necessary fields
            google_id = user_info.get('sub')
            email = user_info.get('email')
            
            if not email:
                current_app.logger.error("Email not provided by Google. Cannot process login.")
                return {"message": "Email not provided by Google. Cannot process login."}, 400
                
            name = user_info.get('name', email.split('@')[0] if email else 'User')
            
            # Find or create user
            user = self._get_or_create_user(google_id, email, name)
            if not isinstance(user, User):
                # If _get_or_create_user returned an error response
                return user
                
            # Generate tokens and return
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
            
            current_app.logger.info(f"User {email} (ID: {user.id}) successfully logged in via Google SSO.")
            return {'access_token': access_token, 'refresh_token': refresh_token}, 200
            
        except Exception as e:
            current_app.logger.error(f"Error during Google authentication: {e}", exc_info=True)
            return {"message": f"Authentication failed: {str(e)}"}, 401
            
    def _get_or_create_user(self, google_id, email, name):
        """Helper method to find or create a user from Google SSO data."""
        # Try to find user by email first
        user = User.query.filter_by(email=email).first()

        if not user and google_id:
            # If no user by email, check by google_sso_id
            user = User.query.filter_by(google_sso_id=google_id).first()

        if not user:
            # Create new user if not found
            try:
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
                db.session.commit()
                current_app.logger.info(f"New user {email} created via Google SSO and committed.")
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error creating new SSO user {email}: {e}", exc_info=True)
                return {"message": "Error creating new user account."}, 500
        else:
            # Update existing user if needed
            updated = False
            
            # Update email if changed in Google
            if user.email != email:
                current_app.logger.info(f"User {user.email} (ID: {user.id}) SSO email changed to {email}. Updating.")
                user.email = email
                updated = True
                
            # Update Google SSO ID if not set
            if not user.google_sso_id and google_id:
                user.google_sso_id = google_id
                updated = True
                
            # Reactivate account if inactive
            if not user.is_active:
                user.is_active = True
                updated = True
                
            if updated:
                try:
                    db.session.commit()
                    current_app.logger.info(f"User {email} (ID: {user.id}) updated and committed (SSO link/activation).")
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"Error updating SSO user {email}: {e}", exc_info=True)
                    return {"message": "Error updating user account during SSO login."}, 500

        # Deny access if account is inactive
        if not user.is_active:
            current_app.logger.warning(f"SSO login attempt for inactive user {email} (ID: {user.id}). Denying access.")
            return {"message": "User account is inactive. Please contact support."}, 403
            
        return user

@ns.route('/google/callback')
class GoogleCallback(Resource):
    @ns.doc(description='Handles the callback from Google after authentication. Issues JWT tokens on success.')
    @ns.expect(google_callback_params)
    @ns.marshal_with(token_model_output) 
    @ns.response(401, 'Authentication failed')
    @ns.response(500, 'SSO Configuration error or internal error')
    def get(self):
        """Process Google OAuth callback, create/login user, and return JWT tokens."""
        try:
            token = oauth.google.authorize_access_token()
        except Exception as e:
            current_app.logger.error(f"Error authorizing Google access token: {e}", exc_info=True)
            return {"status": "error", "message": f"Google authentication failed: {str(e)}"}, 401

        try:
            # Process Google authentication through the service
            user = auth_service.process_google_auth(token)
            
            # Generate JWT tokens
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            
            current_app.logger.info(f"User {user.email} (ID: {user.id}) successfully logged in via Google SSO.")
            return {
                'status': 'success',
                'message': 'Google login successful',
                'access_token': access_token, 
                'refresh_token': refresh_token
            }, 200
            
        except BadRequestError as e:
            return {"status": "error", "message": str(e)}, 400
        except UnauthorizedError as e:
            return {"status": "error", "message": str(e)}, 401
        except ForbiddenError as e:
            return {"status": "error", "message": str(e)}, 403
        except Exception as e:
            current_app.logger.error(f"Error during Google SSO login: {e}", exc_info=True)
            return {"status": "error", "message": "An error occurred during authentication."}, 500