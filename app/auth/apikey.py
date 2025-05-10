# Functions for API Key management (e.g., generation, validation helpers)
# For now, API keys are primarily managed via environment variables / Secret Manager
# and checked in the decorator.

import secrets

def generate_api_key(length=32):
    """Generates a secure random API key."""
    return secrets.token_hex(length)

# Example: If you were to store/manage API keys in the database (not recommended for sensitive keys)
# class ApiKey(db.Model):
#     __tablename__ = 'api_keys'
#     id = db.Column(db.Integer, primary_key=True)
#     key = db.Column(db.String(255), unique=True, nullable=False, index=True)
#     service_name = db.Column(db.String(100), nullable=False) # e.g., 'External Reporting Service'
#     is_active = db.Column(db.Boolean, default=True)
#     created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

#     def __repr__(self):
#         return f'<ApiKey for {self.service_name}>'

# def get_valid_api_key(key_value):
#     # This would involve hashing the input key_value and comparing against stored hashed keys
#     # For simplicity, this example assumes plaintext keys if they were in DB (again, not recommended)
#     return ApiKey.query.filter_by(key=key_value, is_active=True).first()
