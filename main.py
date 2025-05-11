import os
from flask import Flask
from flask_restx import Api
from dotenv import load_dotenv

from config import get_config, config_by_name # Updated import
# Import extensions from app.extensions
from app.extensions import db, migrate, jwt, cors, oauth

# Load environment variables from .env file
load_dotenv()

def create_app(config_name=None):
    """Application factory function."""
    app = Flask(__name__) # Corrected: __name__ not defined, should be __name__

    # Determine configuration to use
    if config_name:
        app.config.from_object(config_by_name[config_name])
    else:
        env_config_name = os.getenv('FLASK_ENV', 'development')
        app.config.from_object(config_by_name.get(env_config_name, config_by_name['default']))
    
    # Ensure SECRET_KEY is set (crucial for sessions used by Authlib)
    if not app.config.get('SECRET_KEY'):
        app.logger.critical("FATAL: SECRET_KEY is not set. Application will not run securely or properly.")
        # In a real scenario, you might raise an error or exit if SECRET_KEY is vital and missing.
        # Forcing a default here is risky, ensure it's set via environment.
        # app.config['SECRET_KEY'] = 'temporary_dev_secret_key' # NOT recommended for production

    # Initialize Flask extensions with the app instance
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}}) # Adjust origins for production
    oauth.init_app(app) # Initialize Authlib's OAuth with the app

    # Initialize Flask-RESTx Api
    api = Api(
        app,
        version='1.0',
        title='Integrated Business Operations Platform API',
        description='API for managing orders, invoicing, payments, contacts, inventory, and more.',
        doc='/doc/',
        prefix='/api/v1'
    )

    # Register Blueprints/Namespaces within app_context
    with app.app_context():
        from app.auth.routes import register_oauth_client # Moved import here to ensure app context
        register_oauth_client(oauth, app.config) # Pass oauth object and app.config

        from app.users.routes import ns as users_ns
        api.add_namespace(users_ns, path='/users')

        from app.auth.routes import ns as auth_ns
        api.add_namespace(auth_ns, path='/auth')
        
        # Placeholder for other modules
        # from app.products.routes import ns as products_ns
        # api.add_namespace(products_ns, path='/products')

    # Health check route
    @app.route('/health')
    def health_check():
        return "Backend is healthy!"

    app.logger.info(f"Application created with configuration: {app.config.get('ENV', config_name)}")
    if app.config.get('GOOGLE_CLIENT_ID'):
        app.logger.info("Google SSO Client ID is configured.")
    else:
        app.logger.warning("Google SSO Client ID is NOT configured. Google SSO will not work.")

    return app

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
