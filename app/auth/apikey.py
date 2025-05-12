# Functions for API Key management with enhanced security
import secrets
import hmac
import hashlib
import base64

def generate_api_key(length=32):
    """Generates a secure random API key."""
    return secrets.token_hex(length)

def hash_api_key(api_key):
    """Creates a secure hash of an API key for storage."""
    salt = secrets.token_bytes(16)
    key_hash = hashlib.pbkdf2_hmac('sha256', api_key.encode(), salt, 100000)
    return base64.b64encode(salt + key_hash).decode()

def verify_api_key(stored_hash, provided_key):
    """Verifies a provided API key against a stored hash."""
    try:
        # Decode the stored hash
        decoded = base64.b64decode(stored_hash.encode())
        salt = decoded[:16]
        stored_key_hash = decoded[16:]
        
        # Hash the provided key with the same salt
        provided_key_hash = hashlib.pbkdf2_hmac('sha256', provided_key.encode(), salt, 100000)
        
        # Compare using constant-time comparison to prevent timing attacks
        return hmac.compare_digest(stored_key_hash, provided_key_hash)
    except Exception:
        return False

# Example implementation for key storage (commented out, as in your original)
# class ApiKey(db.Model):
#     __tablename__ = 'api_keys'
#     id = db.Column(db.Integer, primary_key=True)
#     key_hash = db.Column(db.String(255), nullable=False, index=True)
#     service_name = db.Column(db.String(100), nullable=False)
#     is_active = db.Column(db.Boolean, default=True)
#     created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
#
#     def __repr__(self):
#         return f'<ApiKey for {self.service_name}>'
#
# def get_valid_api_key(key_value):
#     """Check if a provided API key is valid by comparing against stored hashed keys."""
#     for api_key in ApiKey.query.filter_by(is_active=True).all():
#         if verify_api_key(api_key.key_hash, key_value):
#             return api_key
#     return None