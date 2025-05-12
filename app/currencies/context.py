# app/currencies/context.py
from flask import g, request, session, current_app
from functools import wraps
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.users.models import User

def get_current_currency():
    """
    Get the current currency context for the request.
    Order of precedence:
    1. URL parameter (?currency=SGD)
    2. Session variable
    3. User's default currency
    4. System default (SGD)
    """
    # First check if currency is specified in the request
    currency = request.args.get('currency')
    
    # If not in request, check session
    if not currency and 'currency' in session:
        currency = session['currency']
    
    # If not in session, get user's default if authenticated
    if not currency:
        try:
            # Try to get JWT identity without raising exceptions for missing token
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            
            if user_id:
                user = User.query.get(user_id)
                if user:
                    # Get user's default currency
                    from app.currencies.models import UserCurrency
                    default_currency = UserCurrency.query.filter_by(
                        user_id=user.id, 
                        is_default=True
                    ).first()
                    
                    if default_currency:
                        currency = default_currency.currency_code
                    elif user.currency_context:  # Fallback to old field
                        currency = user.currency_context
        except:
            # Handle any exceptions (invalid token, etc)
            pass
    
    # Final fallback to system default
    if not currency:
        currency = current_app.config.get('DEFAULT_CURRENCY', 'SGD')
    
    return currency

def set_currency_context():
    """
    Middleware to set currency context for the current request.
    This should be called from a before_request handler.
    """
    currency = get_current_currency()
    g.currency = currency
    
    # Also store in session for persistence
    if 'currency' not in session or session['currency'] != currency:
        session['currency'] = currency
    
    return currency

def has_currency_access(user_id, currency_code):
    """Check if a user has access to the specified currency."""
    from app.currencies.models import UserCurrency
    return UserCurrency.query.filter_by(
        user_id=user_id,
        currency_code=currency_code
    ).first() is not None

def currency_access_required(fn):
    """
    Decorator to ensure the user has access to the current currency context.
    Must be used after @jwt_required().
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_currency = g.get('currency', get_current_currency())
        user_id = get_jwt_identity()
        
        if not user_id:
            return {'status': 'error', 'message': 'Authentication required'}, 401
        
        if not has_currency_access(user_id, current_currency):
            return {
                'status': 'error', 
                'message': f'You do not have access to currency context: {current_currency}'
            }, 403
        
        return fn(*args, **kwargs)
    return wrapper