from marshmallow import Schema, fields, validate, post_load
# Ensure models are imported after db initialization or within a context where db is available
# from app.extensions import db # Not strictly needed for schema definition unless using SQLAlchemyAutoSchema
from app.users.models import User, Role 

class RoleSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=2, max=64))

class BaseUserSchema(Schema):
    """Base user schema with common fields."""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    email = fields.Email(required=True, validate=validate.Length(max=128))
    google_sso_id = fields.Str(dump_only=True, allow_none=True)
    role_id = fields.Int(load_only=True, allow_none=True, description="ID of the role to assign to the user.")
    role = fields.Nested(RoleSchema, dump_only=True) # For output, show role details
    is_active = fields.Bool(dump_default=True)
    currency_context = fields.Str(validate=validate.OneOf(["SGD", "IDR"]), dump_default="SGD")
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    # Computed fields for output, not part of the model itself
    has_password = fields.Bool(dump_only=True) 
    is_sso_user = fields.Bool(dump_only=True)

class UserSchema(BaseUserSchema):
    """Schema for creating users and for full user representation. Password is required for creation."""
    password = fields.Str(load_only=True, required=True, validate=validate.Length(min=8))

class UserRegistrationSchema(UserSchema):
    """Specifically for admin user registration where password is set."""
    pass # Inherits password requirement

class UserUpdateAdminSchema(BaseUserSchema):
    """Schema for admins updating user info. Password is optional, email can be changed."""
    password = fields.Str(load_only=True, required=False, validate=validate.Length(min=8))
    # Email is already in BaseUserSchema, for admin updates it remains `required=False` implicitly due to partial=True usage in route
    email = fields.Email(required=False, validate=validate.Length(max=128)) # Override to make it not required for partial update

class UserProfileUpdateSchema(Schema):
    """Schema for users updating their own profile (/me endpoint)."""
    name = fields.Str(required=False, validate=validate.Length(min=1, max=128))
    currency_context = fields.Str(required=False, validate=validate.OneOf(["SGD", "IDR"]))
    current_password = fields.Str(load_only=True, required=False) # Required only if new_password is set and user has a password
    new_password = fields.Str(load_only=True, required=False, validate=validate.Length(min=8))

class UserLoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

class TokenSchema(Schema):
    access_token = fields.Str(required=True)
    refresh_token = fields.Str(required=True)
