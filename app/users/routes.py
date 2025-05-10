from flask import request, current_app # Added current_app for logging/config access
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, create_refresh_token

from app.extensions import db # Import db from extensions
from app.users.models import User, Role
from app.users.schemas import (
    UserSchema, UserLoginSchema, RoleSchema, UserRegistrationSchema, 
    UserProfileUpdateSchema, UserUpdateAdminSchema, BaseUserSchema
)
from app.auth.decorators import admin_required

ns = Namespace('users', description='User management operations')

# --- API Models for Swagger/Flask-RESTx ---
# Re-using Marshmallow schema fields for Flask-RESTx models where possible for consistency
# but defining them explicitly for clarity and control over Swagger docs.

role_output_model = ns.model('RoleOutput', {
    'id': fields.Integer(readonly=True, description='Role unique identifier'),
    'name': fields.String(required=True, description='Role name')
})

user_model_output = ns.model('UserOutput', {
    'id': fields.Integer(readonly=True, description='User unique identifier'),
    'name': fields.String(required=True, description='User name'),
    'email': fields.String(required=True, description='User email address'),
    'is_active': fields.Boolean(description='User account status'),
    'currency_context': fields.String(description='User preferred currency (SGD/IDR)'),
    'role': fields.Nested(role_output_model, description='User role', allow_null=True),
    'has_password': fields.Boolean(readonly=True, description='Indicates if the user has a local password set'),
    'is_sso_user': fields.Boolean(readonly=True, description='Indicates if the user is linked with Google SSO'),
    'created_at': fields.DateTime(readonly=True, description='User creation timestamp'),
    'updated_at': fields.DateTime(readonly=True, description='User last update timestamp')
})

# For admin registering a new user
user_registration_input_model = ns.model('UserRegistrationInput', {
    'name': fields.String(required=True, description='User name', example='Jane Doe'),
    'email': fields.String(required=True, description='User email address', example='jane.doe@example.com'),
    'password': fields.String(required=True, description='User password (min 8 characters)', example='securepassword123'),
    'role_id': fields.Integer(description='Role ID to assign to user', allow_null=True, example=1),
    'is_active': fields.Boolean(description='Set user account status', default=True, example=True),
    'currency_context': fields.String(description='User preferred currency (SGD/IDR)', default='SGD', example='SGD')
})

# For admin updating any user's details
user_update_admin_input_model = ns.model('UserUpdateAdminInput', {
    'name': fields.String(required=False, description='User name', example='Jane Smith'),
    'email': fields.String(required=False, description='User email address', example='jane.smith@example.com'),
    'password': fields.String(required=False, description='New user password (min 8 characters, will replace existing)'),
    'role_id': fields.Integer(description='New Role ID for user', allow_null=True, example=2),
    'is_active': fields.Boolean(required=False, description='Set user account status', example=True),
    'currency_context': fields.String(required=False, description='User preferred currency (SGD/IDR)', example='IDR')
})

# For user updating their own profile (/me)
user_profile_update_input_model = ns.model('UserProfileUpdateInput', {
    'name': fields.String(required=False, description='Your name', example='My Updated Name'),
    'currency_context': fields.String(required=False, description='Your preferred currency (SGD/IDR)', example='IDR'),
    'current_password': fields.String(required=False, description='Your current password (needed if changing password and one is set)'),
    'new_password': fields.String(required=False, description='Your new password (min 8 characters)')
})

login_model_input = ns.model('UserLogin', {
    'email': fields.String(required=True, description='User email', example='admin@example.com'),
    'password': fields.String(required=True, description='User password', example='adminpassword')
})

token_model_output = ns.model('TokenOutput', {
    'access_token': fields.String(description='Access token'),
    'refresh_token': fields.String(description='Refresh token', required=False) # Refresh token might not always be returned
})

role_input_model = ns.model('RoleInput', {
    'name': fields.String(required=True, description='Role name', example='Sales')
})

# --- Marshmallow Schema Instances --- 
# (using specific schemas for clarity rather than one generic UserSchema with many variations)\user_registration_schema = UserRegistrationSchema()
user_profile_update_schema = UserProfileUpdateSchema()
user_update_admin_schema = UserUpdateAdminSchema(partial=True) # Admin updates are partial
user_login_schema = UserLoginSchema()
base_user_schema = BaseUserSchema() # For dumping user info
base_users_schema = BaseUserSchema(many=True)
role_schema = RoleSchema()
roles_schema = RoleSchema(many=True)

# --- Helper for computed fields --- 
def _populate_computed_fields(user_obj, user_data_dict):
    """Adds computed fields like has_password and is_sso_user to a user data dictionary."""
    user_data_dict['has_password'] = bool(user_obj.password_hash)
    user_data_dict['is_sso_user'] = bool(user_obj.google_sso_id)
    return user_data_dict

@ns.route('/me')
class UserSelf(Resource):
    @jwt_required()
    @ns.marshal_with(user_model_output)
    def get(self):
        """Get your own user profile"""
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        dumped_data = base_user_schema.dump(user)
        return _populate_computed_fields(user, dumped_data)

    @jwt_required()
    @ns.expect(user_profile_update_input_model) # Corrected model name
    @ns.marshal_with(user_model_output)
    def put(self):
        """Update your own user profile. Password change is restricted for SSO users."""
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        data = request.json

        val_errors = user_profile_update_schema.validate(data)
        if val_errors:
            return val_errors, 400

        user.name = data.get('name', user.name)
        user.currency_context = data.get('currency_context', user.currency_context)

        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if new_password:
            if user.google_sso_id:
                # Strictly enforce: SSO users cannot set/change password via this endpoint as per spec.
                # "API for users to manage their own profile (e.g., change password if not SSO...)"
                return {'message': 'Password management is not available for accounts linked with Google SSO.'}, 403
            
            if not user.password_hash and not current_password:
                # User has no password set, allow setting new_password directly
                pass 
            elif not user.check_password(current_password):
                return {'message': 'Incorrect current password.'}, 400
            
            user.set_password(new_password) # Validation for new_password is in the schema

        try:
            db.session.commit()
        except Exception as e: # Catch potential db errors
            db.session.rollback()
            current_app.logger.error(f"Error updating user profile for {user.email}: {e}", exc_info=True)
            return {"message": "Could not update profile due to a server error."}, 500
        
        dumped_data = base_user_schema.dump(user)
        return _populate_computed_fields(user, dumped_data)

@ns.route('/register') # For Admins
class UserRegister(Resource):
    @ns.expect(user_registration_input_model)
    @ns.marshal_with(user_model_output, code=201)
    @jwt_required()
    @admin_required
    def post(self):
        """Register a new user (Admin action). Requires Admin role."""
        data = request.json
        val_errors = user_registration_schema.validate(data)
        if val_errors:
            return val_errors, 400

        if User.query.filter_by(email=data['email']).first():
            return {'message': 'User already exists with this email'}, 409
        
        new_user = User(
            name=data['name'],
            email=data['email'],
            is_active=data.get('is_active', True),
            currency_context=data.get('currency_context', current_app.config.get('DEFAULT_CURRENCY', 'SGD'))
        )
        new_user.set_password(data['password']) # Password is required by schema

        if 'role_id' in data and data['role_id']:
            role = Role.query.get(data['role_id'])
            if role:
                new_user.role = role
            else:
                return {'message': f"Role with ID {data['role_id']} not found. Cannot assign role." }, 404
        
        try:
            db.session.add(new_user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error registering new user {data['email']}: {e}", exc_info=True)
            return {"message": "Could not register user due to a server error."}, 500

        dumped_data = base_user_schema.dump(new_user)
        return _populate_computed_fields(new_user, dumped_data), 201

@ns.route('/login')
class UserLogin(Resource):
    @ns.expect(login_model_input)
    @ns.marshal_with(token_model_output)
    def post(self):
        """Authenticate user with email/password and return tokens"""
        data = request.json
        val_errors = user_login_schema.validate(data)
        if val_errors:
            return val_errors, 400

        user = User.query.filter_by(email=data['email']).first()
        if user and user.password_hash and user.check_password(data['password']): # Check if password_hash exists
            if not user.is_active:
                return {'message': 'User account is inactive.'}, 403
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
            return {'access_token': access_token, 'refresh_token': refresh_token}, 200
        return {'message': 'Invalid credentials or user not found.'}, 401

@ns.route('/refresh')
class TokenRefresh(Resource):
    @jwt_required(refresh=True)
    @ns.marshal_with(ns.model('AccessTokenOnly', {'access_token': fields.String})) # Specific model for refresh response
    def post(self):
        """Refresh access token using a valid refresh token"""
        current_user_id = get_jwt_identity()
        new_access_token = create_access_token(identity=current_user_id)
        return {'access_token': new_access_token}, 200

@ns.route('/')
class UserList(Resource):
    @ns.marshal_list_with(user_model_output)
    @jwt_required()
    @admin_required
    def get(self):
        """List all users (Admin action)."""
        users = User.query.all()
        dumped_data_list = []
        for user in users:
            dumped_data = base_user_schema.dump(user)
            dumped_data_list.append(_populate_computed_fields(user, dumped_data))
        return dumped_data_list, 200

@ns.route('/<int:user_id>')
@ns.response(404, 'User not found')
class UserResource(Resource): # Renamed for clarity from UserDetail
    @ns.marshal_with(user_model_output)
    @jwt_required()
    def get(self, user_id):
        """Get a specific user's details. Admins can get any; users can get their own."""
        requesting_user_id = get_jwt_identity()
        requesting_user = User.query.get(requesting_user_id)
        
        if not (requesting_user.role and requesting_user.role.name == 'Admin') and requesting_user_id != user_id:
            ns.abort(403, message="Forbidden: You can only view your own profile or you lack admin privileges.")
        
        user = User.query.get_or_404(user_id)
        dumped_data = base_user_schema.dump(user)
        return _populate_computed_fields(user, dumped_data)

    @ns.expect(user_update_admin_input_model) # Corrected model name
    @ns.marshal_with(user_model_output)
    @jwt_required()
    @admin_required
    def put(self, user_id):
        """Update a user's details (Admin action)."""
        user = User.query.get_or_404(user_id)
        data = request.json
        val_errors = user_update_admin_schema.validate(data) # Uses partial=True from schema definition
        if val_errors:
            return val_errors, 400

        user.name = data.get('name', user.name)
        new_email = data.get('email')
        if new_email and new_email != user.email:
            if User.query.filter(User.email == new_email, User.id != user_id).first():
                return {'message': 'Email already in use by another account'}, 409
            user.email = new_email
        
        if 'is_active' in data:
            user.is_active = data['is_active']
        user.currency_context = data.get('currency_context', user.currency_context)

        if 'role_id' in data:
            if data['role_id'] is not None:
                role = Role.query.get(data['role_id'])
                if not role:
                    return {'message': f"Role with ID {data['role_id']} not found"}, 404
                user.role_id = role.id # Explicitly set role_id
            else:
                user.role_id = None # Allow unassigning role

        if 'password' in data and data['password']:
            user.set_password(data['password']) # New password validation is in schema
        elif 'password' in data and not data['password']:
             # If admin explicitly sends empty string for password, consider clearing it
             # This might be desired to force SSO or reset. For now, we only set if non-empty.
             pass 

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating user {user.email} (admin): {e}", exc_info=True)
            return {"message": "Could not update user due to a server error."}, 500
        
        dumped_data = base_user_schema.dump(user)
        return _populate_computed_fields(user, dumped_data)

    @jwt_required()
    @admin_required
    @ns.response(204, 'User deleted successfully')
    @ns.response(403, 'Deletion forbidden (e.g., deleting self, deleting system-critical user)')
    def delete(self, user_id):
        """Delete a user (Admin action)."""
        requesting_user_id = get_jwt_identity()
        if user_id == requesting_user_id:
            return {"message": "Admins cannot delete their own active account via this endpoint."}, 403
            
        user = User.query.get_or_404(user_id)
        # Add any other critical user deletion prevention logic here (e.g., if user is last admin)
        try:
            db.session.delete(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting user {user.email}: {e}", exc_info=True)
            return {"message": "Could not delete user due to a server error."}, 500
        return '', 204

# --- Roles Management ---
@ns.route('/roles')
class RoleList(Resource):
    @ns.marshal_list_with(role_output_model)
    @jwt_required()
    @admin_required
    def get(self):
        """List all roles (Admin action)."""
        roles = Role.query.all()
        return roles_schema.dump(roles), 200 # roles_schema is RoleSchema(many=True)

    @ns.expect(role_input_model)
    @ns.marshal_with(role_output_model, code=201)
    @jwt_required()
    @admin_required
    def post(self):
        """Create a new role (Admin action)."""
        data = request.json
        val_errors = role_schema.validate(data)
        if val_errors:
            return val_errors, 400
        
        if Role.query.filter_by(name=data['name']).first():
            return {'message': 'Role with this name already exists'}, 409
        
        new_role = Role(name=data['name'])
        try:
            db.session.add(new_role)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating role {data['name']}: {e}", exc_info=True)
            return {"message": "Could not create role due to a server error."}, 500
        return role_schema.dump(new_role), 201

@ns.route('/roles/<int:role_id>')
@ns.response(404, 'Role not found')
class RoleResource(Resource): # Renamed for clarity
    @ns.marshal_with(role_output_model)
    @jwt_required()
    @admin_required
    def get(self, role_id):
        """Get role details (Admin action)."""
        role = Role.query.get_or_404(role_id)
        return role_schema.dump(role), 200
    
    @ns.expect(role_input_model) 
    @ns.marshal_with(role_output_model)
    @jwt_required()
    @admin_required
    def put(self, role_id):
        """Update role name (Admin action)."""
        role = Role.query.get_or_404(role_id)
        data = request.json
        val_errors = role_schema.validate(data)
        if val_errors:
            return val_errors, 400

        new_name = data.get('name')
        if new_name and new_name != role.name and Role.query.filter(Role.name == new_name, Role.id != role_id).first():
            return {'message': 'Role name already in use'}, 409
        
        role.name = new_name if new_name else role.name
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating role {role.name}: {e}", exc_info=True)
            return {"message": "Could not update role due to a server error."}, 500
        return role_schema.dump(role), 200

    @jwt_required()
    @admin_required
    @ns.response(204, 'Role deleted successfully')
    @ns.response(400, 'Cannot delete role (e.g., role in use)')
    @ns.response(403, 'Cannot delete critical role (e.g., Admin)')
    def delete(self, role_id):
        """Delete a role (Admin action)."""
        role = Role.query.get_or_404(role_id)
        if role.name.lower() == 'admin': 
            return {"message": "Cannot delete the core 'Admin' role."}, 403
        if role.name.lower() == current_app.config.get('DEFAULT_USER_ROLE', 'User').lower():
             return {"message": f"Cannot delete the default system role '{role.name}'."}, 403

        if role.users.first(): # Check if any user has this role
             return {'message': f"Cannot delete role '{role.name}', it is currently assigned to users. Please reassign users first." }, 400

        try:
            db.session.delete(role)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting role {role.name}: {e}", exc_info=True)
            return {"message": "Could not delete role due to a server error."}, 500
        return '', 204
