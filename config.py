import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables at the beginning

class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY') # No default, should be set in .env
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') # No default

    # --- Google OAuth Credentials & Settings ---
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
    GOOGLE_OAUTH_SCOPES = ["openid", "email", "profile"]
    # GOOGLE_REDIRECT_URI is set per environment or by env var
    GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI')

    # Default operating currency
    DEFAULT_CURRENCY = os.environ.get('DEFAULT_CURRENCY', 'SGD')
    DEFAULT_USER_ROLE = os.environ.get('DEFAULT_USER_ROLE', 'User') # For new SSO users

    # API Keys (example, load more robustly if many keys)
    SERVER_API_KEYS = {
        key_name: os.environ.get(key_name)
        for key_name in os.environ
        if key_name.startswith('SERVER_API_KEY_NAME_') and os.environ.get(f"SERVER_API_KEY_VALUE_{key_name.split('SERVER_API_KEY_NAME_')[1]}")
    } # This is a bit complex, consider a simpler pattern or dedicated parsing
    # A simpler way for a few keys:
    # SERVER_API_KEY_1 = os.environ.get('SERVER_API_KEY_1') 

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URI', os.environ.get('SQLALCHEMY_DATABASE_URI'))
    SQLALCHEMY_ECHO = os.environ.get('SQLALCHEMY_ECHO', 'False').lower() == 'true' # Enable SQL query logging if set
    
    # Override GOOGLE_REDIRECT_URI for local development if not set by environment variable
    if not Config.GOOGLE_REDIRECT_URI:
        GOOGLE_REDIRECT_URI = 'http://localhost:5000/api/v1/auth/google/callback'
    
    ENV = 'development' # Explicitly set ENV for clarity if needed

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('PROD_DATABASE_URI', os.environ.get('SQLALCHEMY_DATABASE_URI'))
    # GOOGLE_REDIRECT_URI MUST be set in environment for production (e.g., to an HTTPS endpoint)
    if not Config.GOOGLE_REDIRECT_URI:
        # This will cause an issue at runtime if not set, which is desired to enforce configuration.
        pass 
    ENV = 'production'

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URI', 'sqlite:///:memory:')
    JWT_SECRET_KEY = 'test_jwt_secret_key' # Override for test consistency
    SECRET_KEY = 'test_secret_key'       # Override for test consistency
    GOOGLE_CLIENT_ID = 'test_google_client_id'
    GOOGLE_CLIENT_SECRET = 'test_google_client_secret'
    GOOGLE_REDIRECT_URI = 'http://localhost/test_callback'
    DEFAULT_USER_ROLE = 'TestUser'
    ENV = 'testing'

# Dictionary to map config names to their classes
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig # Default to development if FLASK_ENV is not set or invalid
}

# Helper function to get the config object based on FLASK_ENV or a passed name
# This function is not strictly needed if create_app directly accesses config_by_name
# but can be useful if config is needed outside the app factory.
# def get_current_config(config_name_override=None):
#     if config_name_override:
#         return config_by_name.get(config_name_override, DevelopmentConfig)
#     flask_env = os.getenv('FLASK_ENV', 'development')
#     return config_by_name.get(flask_env, DevelopmentConfig)
