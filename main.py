import os
from flask import Flask, jsonify, request
from flask_restx import Api
from dotenv import load_dotenv

from config import get_config, config_by_name
from app.extensions import db, migrate, jwt, oauth
from flask_cors import CORS
from app.core.error_handlers import register_error_handlers
from app.core.logging import configure_logging
from app.auth.routes import register_oauth_client

# Load environment variables from .env file
load_dotenv()

def create_app(config_name=None):
    """Application factory function."""
    app = Flask(__name__)

    # Determine configuration to use
    if config_name:
        app.config.from_object(config_by_name[config_name])
    else:
        env_config_name = os.getenv('FLASK_ENV', 'development')
        app.config.from_object(config_by_name.get(env_config_name, config_by_name['default']))
    
    # Ensure SECRET_KEY is set (crucial for sessions used by Authlib)
    if not app.config.get('SECRET_KEY'):
        app.logger.critical("FATAL: SECRET_KEY is not set. Application will not run securely or properly.")

    # Specific JWT configuration
    if not app.config.get('JWT_SECRET_KEY'):
        app.logger.warning("JWT_SECRET_KEY not set. Using SECRET_KEY for JWT instead.")
        app.config['JWT_SECRET_KEY'] = app.config.get('SECRET_KEY')
        
    # Force JWT identity to be handled as string
    app.config['JWT_IDENTITY_CLAIM'] = 'sub'

    # Enable more detailed error messages in development
    if app.config.get('ENV') == 'development':
        app.config['PROPAGATE_EXCEPTIONS'] = True

    # Initialize Flask extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Initialize CORS with proper configuration - only configure it ONCE
    CORS(app, 
        resources={r"/*": {
            "origins": "*",
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        }}
    )
    
    oauth.init_app(app) # Initialize Authlib's OAuth with the app

    # Register error handlers
    register_error_handlers(app)
    
    # Configure logging
    configure_logging(app)
    
    # Set up JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'status': 'error',
            'message': 'The token has expired',
            'error': 'token_expired'
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'status': 'error',
            'message': 'Signature verification failed',
            'error': 'invalid_token'
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'status': 'error',
            'message': 'Request does not contain an access token',
            'error': 'authorization_required'
        }), 401

    # Initialize Flask-RESTx Api
    api = Api(
        app,
        version='1.0',
        title='Integrated Business Operations Platform API',
        description='API for managing orders, invoicing, payments, contacts, inventory, and more.',
        doc='/api/v1/doc/',  # Move doc route under the API prefix
        prefix='/api/v1'
    )

    # Simple health check route
    @app.route('/health')
    def health_check():
        return jsonify({
            "status": "healthy", 
            "message": "API is running",
            "environment": app.config.get('ENV', 'development')
        })

    # Register Blueprints/Namespaces within app_context
    with app.app_context():
        # Register OAuth client
        register_oauth_client(oauth, app.config)

        # Register API namespaces
        from app.users.routes import ns as users_ns
        api.add_namespace(users_ns, path='/users')

        from app.auth.routes import ns as auth_ns
        api.add_namespace(auth_ns, path='/auth')

        # Import the currencies namespace
        from app.currencies.routes import ns as currencies_ns, initialize_currencies
        api.add_namespace(currencies_ns, path='/currencies')

        # Initialize currencies after all namespaces are registered (around line 82-85)
        try:
            initialize_currencies()
        except Exception as e:
            app.logger.error(f"Error initializing currencies: {e}")
        
        # Create default admin user if no users exist
        create_default_admin(app)

    app.logger.info(f"Application created with configuration: {app.config.get('ENV', config_name)}")
    
    # Check Google SSO configuration
    google_client_id = app.config.get('GOOGLE_CLIENT_ID')
    if google_client_id and len(str(google_client_id)) > 10:  # Simple check for a valid-looking ID
        app.logger.info("Google SSO Client ID is configured.")
    else:
        app.logger.warning("Google SSO Client ID is NOT configured or invalid. Google SSO will not work.")

    return app

def create_default_admin(app):
    """Create a default admin user if no users exist in the database."""
    with app.app_context():
        try:
            from app.users.models import User, Role
            
            # Check if we have any users
            user_count = User.query.count()
            
            if user_count == 0:
                # Get admin credentials from environment variables (.env file)
                admin_email = os.environ.get('DEFAULT_ADMIN_EMAIL')
                admin_password = os.environ.get('DEFAULT_ADMIN_PASSWORD')
                
                # Only proceed if credentials are provided
                if not admin_email or not admin_password:
                    app.logger.warning("DEFAULT_ADMIN_EMAIL or DEFAULT_ADMIN_PASSWORD not set in .env file. Skipping default admin creation.")
                    return
                
                app.logger.info(f"No users found in database. Creating default admin user with email: {admin_email}...")
                
                # Create admin role if it doesn't exist
                admin_role = Role.query.filter_by(name='Admin').first()
                if not admin_role:
                    admin_role = Role(name='Admin')
                    db.session.add(admin_role)
                    db.session.commit()
                    app.logger.info("Admin role created")
                
                # Create admin user
                admin = User(
                    name='Admin User',
                    email=admin_email,
                    is_active=True,
                    role=admin_role,
                    currency_context=app.config.get('DEFAULT_CURRENCY', 'SGD')
                )
                admin.set_password(admin_password)
                db.session.add(admin)
                db.session.commit()
                
                app.logger.info(f"Default admin user created with email: {admin_email}")
                app.logger.warning("SECURITY NOTICE: Default admin user created with preset password. Please change it immediately after login.")
            else:
                app.logger.info(f"Database already has {user_count} users. Skipping default admin creation.")
                
        except Exception as e:
            app.logger.error(f"Error creating default admin user: {e}")
            # Don't raise the exception - let the application start anyway

# Gunicorn and Flask CLI will use create_app() without arguments,
# relying on FLASK_ENV or the default.
if __name__ == '__main__':
    # When running directly (python main.py), use FLASK_ENV or default to 'development'
    # The create_app function already handles fetching the config based on FLASK_ENV or a default.
    current_app = create_app() 
    current_app.run(
        debug=current_app.config.get('DEBUG', False), 
        port=int(os.environ.get("PORT", 5000))
    )