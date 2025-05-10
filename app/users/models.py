from app import db # Assuming db is initialized in the main app.py or via a shared extension module
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    users = db.relationship('User', backref='role', lazy='dynamic') # one-to-many

    def __repr__(self):
        return f'<Role {self.name}>'

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255))
    google_sso_id = db.Column(db.String(255), unique=True, nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=True) # Can be nullable if role assignment is optional or delayed
    is_active = db.Column(db.Boolean, default=True)
    currency_context = db.Column(db.String(3), default='SGD') # E.g., SGD, IDR
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

# Permissions could be defined here or in a separate model/table
# For RBAC, permissions are typically associated with roles.
# Example for future extension:
# class Permission(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(255), unique=True, nullable=False) # e.g., 'create_user', 'edit_product'

# roles_permissions = db.Table('roles_permissions',
#     db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
#     db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True)
# )
