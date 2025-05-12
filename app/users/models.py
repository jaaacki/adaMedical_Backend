from app.extensions import db
import bcrypt
import datetime
import os

# Create a standardized password hashing method using bcrypt
def hash_password(password):
    """Hash password using bcrypt with consistent encoding."""
    if isinstance(password, str):
        password = password.encode('utf-8')
    return bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

def verify_password(stored_hash, password):
    """Verify password against stored hash with consistent encoding."""
    if not stored_hash:
        return False
    
    # Ensure password is bytes
    if isinstance(password, str):
        password = password.encode('utf-8')
    
    # Ensure stored_hash is bytes 
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode('utf-8')
    
    try:
        # Directly use bcrypt for verification
        return bcrypt.checkpw(password, stored_hash)
    except Exception as e:
        # If there's any error, log it and return False
        print(f"Password verification error: {str(e)}")
        return False

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
        """Set the password hash using bcrypt."""
        self.password_hash = hash_password(password)

    def check_password(self, password):
        """Check if the provided password matches the stored hash."""
        return verify_password(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'
    
# Add this to the User class:
currencies = db.relationship('UserCurrency', back_populates='user', cascade='all, delete-orphan')

# Add this method to the User class:
def get_current_currency(self):
    """Get the user's current working currency code."""
    default_currency = UserCurrency.query.filter_by(
        user_id=self.id, 
        is_default=True
    ).first()
    
    if default_currency:
        return default_currency.currency_code
    
    # Fallback to the old currency_context field for backward compatibility
    if self.currency_context:
        return self.currency_context
    
    # Final fallback to system default
    from flask import current_app
    return current_app.config.get('DEFAULT_CURRENCY', 'SGD')

def get_assigned_currencies(self):
    """Get list of currency codes assigned to this user."""
    user_currencies = UserCurrency.query.filter_by(user_id=self.id).all()
    return [uc.currency_code for uc in user_currencies]

def has_currency_access(self, currency_code):
    """Check if user has access to a specific currency."""
    return UserCurrency.query.filter_by(
        user_id=self.id,
        currency_code=currency_code
    ).first() is not None