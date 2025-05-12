# app/currencies/routes.py
from flask import request, current_app, g
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.auth.decorators import admin_required

# Create the currencies namespace
ns = Namespace('currencies', description='Currency management operations')

# API Models for Swagger documentation
currency_model = ns.model('Currency', {
    'code': fields.String(required=True, description='Currency code (e.g., SGD)'),
    'name': fields.String(required=True, description='Currency name'),
    'symbol': fields.String(required=True, description='Currency symbol'),
    'is_active': fields.Boolean(description='Whether currency is active'),
    'created_at': fields.DateTime(readonly=True),
    'updated_at': fields.DateTime(readonly=True)
})

user_currency_model = ns.model('UserCurrency', {
    'id': fields.Integer(readonly=True, description='Unique identifier'),
    'user_id': fields.Integer(required=True, description='User ID'),
    'currency_code': fields.String(required=True, description='Currency code'),
    'is_default': fields.Boolean(description='Whether this is user\'s default currency'),
    'created_at': fields.DateTime(readonly=True),
    'updated_at': fields.DateTime(readonly=True)
})

user_currency_detail_model = ns.model('UserCurrencyDetail', {
    'id': fields.Integer(readonly=True, description='Unique identifier'),
    'user_id': fields.Integer(required=True, description='User ID'),
    'currency_code': fields.String(required=True, description='Currency code'),
    'is_default': fields.Boolean(description='Whether this is user\'s default currency'),
    'currency': fields.Nested(currency_model, description='Currency details'),
    'created_at': fields.DateTime(readonly=True),
    'updated_at': fields.DateTime(readonly=True)
})

# Success response model
success_model = ns.model('SuccessResponse', {
    'status': fields.String(description='Operation status', enum=['success']),
    'message': fields.String(description='Success message')
})

# Currency Models (to be moved to models.py in a real implementation)
class Currency(db.Model):
    """Model for available currencies in the system."""
    __tablename__ = 'currencies'
    
    code = db.Column(db.String(3), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    symbol = db.Column(db.String(5), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    
    def __repr__(self):
        return f'<Currency {self.code}>'

class UserCurrency(db.Model):
    """Model for user currency assignments."""
    __tablename__ = 'user_currencies'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    currency_code = db.Column(db.String(3), db.ForeignKey('currencies.code', ondelete='CASCADE'), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    
    # Define relationship to Currency
    currency = db.relationship('Currency', lazy='joined')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'currency_code', name='uq_user_currency'),
    )
    
    def __repr__(self):
        return f'<UserCurrency user_id={self.user_id} currency={self.currency_code}>'

# Routes
@ns.route('/')
class CurrencyList(Resource):
    @ns.marshal_list_with(currency_model)
    @ns.response(200, 'Success')
    @jwt_required()
    def get(self):
        """List all available currencies."""
        return Currency.query.filter_by(is_active=True).all()
    
    @ns.expect(currency_model)
    @ns.marshal_with(currency_model, code=201)
    @ns.response(201, 'Currency created')
    @ns.response(400, 'Validation error')
    @ns.response(409, 'Currency already exists')
    @jwt_required()
    @admin_required
    def post(self):
        """Create a new currency (Admin only)."""
        data = request.json
        
        # Check if currency already exists
        if Currency.query.get(data['code']):
            return {'status': 'error', 'message': f"Currency with code {data['code']} already exists"}, 409
        
        # Create currency
        new_currency = Currency(
            code=data['code'],
            name=data['name'],
            symbol=data['symbol'],
            is_active=data.get('is_active', True)
        )
        
        db.session.add(new_currency)
        db.session.commit()
        
        return new_currency, 201

@ns.route('/<string:code>')
@ns.response(404, 'Currency not found')
class CurrencyDetail(Resource):
    @ns.marshal_with(currency_model)
    @ns.response(200, 'Success')
    @jwt_required()
    def get(self, code):
        """Get a specific currency by code."""
        currency = Currency.query.get_or_404(code)
        return currency
    
    @ns.expect(currency_model)
    @ns.marshal_with(currency_model)
    @ns.response(200, 'Currency updated')
    @jwt_required()
    @admin_required
    def put(self, code):
        """Update a currency (Admin only)."""
        currency = Currency.query.get_or_404(code)
        data = request.json
        
        if 'name' in data:
            currency.name = data['name']
        
        if 'symbol' in data:
            currency.symbol = data['symbol']
        
        if 'is_active' in data:
            currency.is_active = data['is_active']
        
        db.session.commit()
        return currency

    @ns.response(200, 'Currency deleted')
    @jwt_required()
    @admin_required
    def delete(self, code):
        """Delete a currency (Admin only)."""
        currency = Currency.query.get_or_404(code)
        
        # Check if the currency is in use
        if UserCurrency.query.filter_by(currency_code=code).first():
            return {'status': 'error', 'message': 'Cannot delete currency that is assigned to users'}, 400
        
        db.session.delete(currency)
        db.session.commit()
        
        return {'status': 'success', 'message': f'Currency {code} deleted'}

@ns.route('/user/currencies')
class UserCurrencyList(Resource):
    @ns.marshal_list_with(user_currency_detail_model)
    @ns.response(200, 'Success')
    @jwt_required()
    def get(self):
        """Get currencies assigned to the current user."""
        user_id = get_jwt_identity()
        user_currencies = UserCurrency.query.filter_by(user_id=user_id).all()
        return user_currencies
    
    @ns.expect(ns.model('AssignCurrency', {
        'currency_code': fields.String(required=True, description='Currency code to assign'),
        'is_default': fields.Boolean(default=False)
    }))
    @ns.marshal_with(user_currency_model, code=201)
    @ns.response(201, 'Currency assigned')
    @ns.response(400, 'Validation error')
    @ns.response(404, 'Currency not found')
    @ns.response(409, 'Currency already assigned')
    @jwt_required()
    def post(self):
        """Assign a currency to current user."""
        user_id = get_jwt_identity()
        data = request.json
        
        currency_code = data.get('currency_code')
        if not currency_code:
            return {'status': 'error', 'message': 'currency_code is required'}, 400
        
        # Check if currency exists
        currency = Currency.query.get(currency_code)
        if not currency:
            return {'status': 'error', 'message': f'Currency {currency_code} not found'}, 404
        
        # Check if already assigned
        existing = UserCurrency.query.filter_by(
            user_id=user_id,
            currency_code=currency_code
        ).first()
        
        if existing:
            return {
                'status': 'error',
                'message': f'Currency {currency_code} is already assigned to your account'
            }, 409
        
        # Create assignment
        new_assignment = UserCurrency(
            user_id=user_id,
            currency_code=currency_code,
            is_default=data.get('is_default', False)
        )
        
        # If setting as default, unset existing default
        if new_assignment.is_default:
            UserCurrency.query.filter_by(
                user_id=user_id,
                is_default=True
            ).update({'is_default': False})
        
        db.session.add(new_assignment)
        db.session.commit()
        
        return new_assignment, 201

@ns.route('/user/default')
class UserDefaultCurrency(Resource):
    @ns.expect(ns.model('SetDefaultCurrency', {
        'currency_code': fields.String(required=True, description='Currency code to set as default')
    }))
    @ns.marshal_with(success_model)
    @ns.response(200, 'Default currency updated')
    @ns.response(400, 'Currency not assigned to user')
    @jwt_required()
    def put(self):
        """Set a user's default currency."""
        user_id = get_jwt_identity()
        data = request.json
        
        currency_code = data.get('currency_code')
        if not currency_code:
            return {'status': 'error', 'message': 'currency_code is required'}, 400
        
        # Make sure the currency is assigned to the user
        user_currency = UserCurrency.query.filter_by(
            user_id=user_id,
            currency_code=currency_code
        ).first()
        
        if not user_currency:
            return {
                'status': 'error',
                'message': f'Currency {currency_code} is not assigned to your account'
            }, 400
        
        # Update default currency
        # First, unset all defaults
        UserCurrency.query.filter_by(
            user_id=user_id,
            is_default=True
        ).update({'is_default': False})
        
        # Set the new default
        user_currency.is_default = True
        
        # Also update user.currency_context for backward compatibility
        from app.users.models import User
        user = User.query.get(user_id)
        if user:
            user.currency_context = currency_code
        
        db.session.commit()
        
        return {
            'status': 'success',
            'message': f'Default currency set to {currency_code}'
        }

# Admin routes for user currency management
@ns.route('/admin/users/<int:user_id>/currencies')
class AdminUserCurrencyList(Resource):
    @ns.marshal_list_with(user_currency_detail_model)
    @ns.response(200, 'Success')
    @ns.response(403, 'Admin access required')
    @ns.response(404, 'User not found')
    @jwt_required()
    @admin_required
    def get(self, user_id):
        """Get currencies assigned to a specific user (Admin only)."""
        # Verify user exists
        from app.users.models import User
        user = User.query.get_or_404(user_id)
        
        user_currencies = UserCurrency.query.filter_by(user_id=user_id).all()
        return user_currencies
    
    @ns.expect(ns.model('AdminAssignCurrency', {
        'currency_code': fields.String(required=True, description='Currency code to assign'),
        'is_default': fields.Boolean(default=False)
    }))
    @ns.marshal_with(user_currency_model, code=201)
    @ns.response(201, 'Currency assigned to user')
    @ns.response(400, 'Validation error')
    @ns.response(403, 'Admin access required')
    @ns.response(404, 'User or currency not found')
    @ns.response(409, 'Currency already assigned to user')
    @jwt_required()
    @admin_required
    def post(self, user_id):
        """Assign a currency to a user (Admin only)."""
        # Verify user exists
        from app.users.models import User
        user = User.query.get_or_404(user_id)
        
        data = request.json
        currency_code = data.get('currency_code')
        
        if not currency_code:
            return {'status': 'error', 'message': 'currency_code is required'}, 400
        
        # Check if currency exists
        currency = Currency.query.get(currency_code)
        if not currency:
            return {'status': 'error', 'message': f'Currency {currency_code} not found'}, 404
        
        # Check if already assigned
        existing = UserCurrency.query.filter_by(
            user_id=user_id,
            currency_code=currency_code
        ).first()
        
        if existing:
            return {
                'status': 'error',
                'message': f'Currency {currency_code} is already assigned to user {user_id}'
            }, 409
        
        # Create assignment
        new_assignment = UserCurrency(
            user_id=user_id,
            currency_code=currency_code,
            is_default=data.get('is_default', False)
        )
        
        # If setting as default, unset existing default
        if new_assignment.is_default:
            UserCurrency.query.filter_by(
                user_id=user_id,
                is_default=True
            ).update({'is_default': False})
            
            # Also update user.currency_context for backward compatibility
            user.currency_context = currency_code
        
        db.session.add(new_assignment)
        db.session.commit()
        
        return new_assignment, 201

@ns.route('/admin/users/<int:user_id>/currencies/<string:currency_code>')
class AdminUserCurrencyDetail(Resource):
    @ns.marshal_with(user_currency_detail_model)
    @ns.response(200, 'Success')
    @ns.response(403, 'Admin access required')
    @ns.response(404, 'User currency assignment not found')
    @jwt_required()
    @admin_required
    def get(self, user_id, currency_code):
        """Get details of a specific currency assignment for a user (Admin only)."""
        user_currency = UserCurrency.query.filter_by(
            user_id=user_id,
            currency_code=currency_code
        ).first_or_404()
        
        return user_currency
    
    @ns.expect(ns.model('UpdateUserCurrency', {
        'is_default': fields.Boolean(description='Set as default currency')
    }))
    @ns.marshal_with(user_currency_detail_model)
    @ns.response(200, 'User currency updated')
    @ns.response(403, 'Admin access required')
    @ns.response(404, 'User currency assignment not found')
    @jwt_required()
    @admin_required
    def put(self, user_id, currency_code):
        """Update currency assignment settings for a user (Admin only)."""
        data = request.json
        
        # Get the assignment
        user_currency = UserCurrency.query.filter_by(
            user_id=user_id,
            currency_code=currency_code
        ).first_or_404()
        
        # Update default setting if requested
        if 'is_default' in data and data['is_default'] and not user_currency.is_default:
            # Unset current default
            UserCurrency.query.filter_by(
                user_id=user_id,
                is_default=True
            ).update({'is_default': False})
            
            # Set this as default
            user_currency.is_default = True
            
            # Also update user.currency_context for backward compatibility
            from app.users.models import User
            user = User.query.get(user_id)
            if user:
                user.currency_context = currency_code
        
        db.session.commit()
        return user_currency
    
    @ns.response(200, 'Currency assignment removed')
    @ns.response(400, 'Cannot remove default currency')
    @ns.response(403, 'Admin access required')
    @ns.response(404, 'User currency assignment not found')
    @jwt_required()
    @admin_required
    def delete(self, user_id, currency_code):
        """Remove a currency assignment from a user (Admin only)."""
        # Get the assignment
        user_currency = UserCurrency.query.filter_by(
            user_id=user_id,
            currency_code=currency_code
        ).first_or_404()
        
        # Don't allow removing the default currency
        if user_currency.is_default:
            return {
                'status': 'error',
                'message': 'Cannot remove a user\'s default currency. Set another currency as default first.'
            }, 400
        
        # Don't allow removing if it's the user's only currency
        count = UserCurrency.query.filter_by(user_id=user_id).count()
        if count <= 1:
            return {
                'status': 'error',
                'message': 'Cannot remove a user\'s only currency assignment.'
            }, 400
        
        db.session.delete(user_currency)
        db.session.commit()
        
        return {'status': 'success', 'message': f'Currency {currency_code} removed from user {user_id}'}

# Initialize with default currencies
def initialize_currencies():
    """Initialize the currencies table with default values."""
    # Default currencies to create if they don't exist
    default_currencies = [
        {'code': 'SGD', 'name': 'Singapore Dollar', 'symbol': 'S$'},
        {'code': 'IDR', 'name': 'Indonesian Rupiah', 'symbol': 'Rp'},
        {'code': 'USD', 'name': 'US Dollar', 'symbol': '$'},
        {'code': 'EUR', 'name': 'Euro', 'symbol': '€'},
        {'code': 'GBP', 'name': 'British Pound', 'symbol': '£'},
        {'code': 'JPY', 'name': 'Japanese Yen', 'symbol': '¥'},
        {'code': 'AUD', 'name': 'Australian Dollar', 'symbol': 'A$'},
        {'code': 'CNY', 'name': 'Chinese Yuan', 'symbol': '¥'},
    ]
    
    # Create each currency if it doesn't exist
    for curr_data in default_currencies:
        existing = Currency.query.get(curr_data['code'])
        if not existing:
            currency = Currency(
                code=curr_data['code'],
                name=curr_data['name'],
                symbol=curr_data['symbol'],
                is_active=True
            )
            db.session.add(currency)
    
    # Commit all changes
    try:
        db.session.commit()
        current_app.logger.info("Default currencies initialized.")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error initializing currencies: {e}")