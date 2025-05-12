# app/currencies/routes.py
from flask import request, current_app, g
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.currencies.models import Currency, UserCurrency
from app.users.models import User
from app.auth.decorators import admin_required
from app.currencies.context import currency_access_required

ns = Namespace('currencies', description='Currency management')

# API Models for Swagger docs
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

# Response models
success_model = ns.model('SuccessResponse', {
    'status': fields.String(description='Operation status', enum=['success']),
    'message': fields.String(description='Success message')
})

# Currencies CRUD endpoints
@ns.route('/')
class CurrencyList(Resource):
    @ns.marshal_list_with(currency_model)
    @ns.response(200, 'Success')
    @jwt_required()
    def get(self):
        """List all currencies."""
        # Show only active currencies to non-admin users
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Use is_admin check (either Admin role or broader check)
        if user.role and user.role.name in ['Admin', 'Administrator', 'Admininstrator']:
            return Currency.query.all()
        else:
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
        
        # Validate code format
        if not data['code'] or len(data['code']) != 3:
            return {'status': 'error', 'message': 'Currency code must be exactly 3 characters'}, 400
        
        new_currency = Currency(
            code=data['code'],
            name=data['name'],
            symbol=data['symbol'],
            is_active=data.get('is_active', True)
        )
        
        try:
            db.session.add(new_currency)
            db.session.commit()
            return new_currency, 201
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating currency: {str(e)}")
            return {'status': 'error', 'message': 'Could not create currency'}, 500

@ns.route('/<string:code>')
@ns.response(404, 'Currency not found')
class CurrencyDetail(Resource):
    @ns.marshal_with(currency_model)
    @ns.response(200, 'Success')
    @jwt_required()
    def get(self, code):
        """Get details of a specific currency."""
        currency = Currency.query.get_or_404(code)
        return currency
    
    @ns.expect(currency_model)
    @ns.marshal_with(currency_model)
    @ns.response(200, 'Currency updated')
    @ns.response(400, 'Validation error')
    @jwt_required()
    @admin_required
    def put(self, code):
        """Update a currency (Admin only)."""
        currency = Currency.query.get_or_404(code)
        data = request.json
        
        # Update fields
        if 'name' in data:
            currency.name = data['name']
        if 'symbol' in data:
            currency.symbol = data['symbol']
        if 'is_active' in data:
            currency.is_active = data['is_active']
        
        try:
            db.session.commit()
            return currency, 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating currency: {str(e)}")
            return {'status': 'error', 'message': 'Could not update currency'}, 500
    
    @ns.response(200, 'Currency deleted')
    @ns.response(400, 'Cannot delete currency that is in use')
    @jwt_required()
    @admin_required
    def delete(self, code):
        """Delete a currency (Admin only)."""
        currency = Currency.query.get_or_404(code)
        
        # Check if currency is in use by any user
        if UserCurrency.query.filter_by(currency_code=code).count() > 0:
            return {
                'status': 'error', 
                'message': 'Cannot delete currency that is assigned to users'
            }, 400
            
        # Check if it's the system default currency
        default_currency = current_app.config.get('DEFAULT_CURRENCY', 'SGD')
        if code == default_currency:
            return {
                'status': 'error',
                'message': f'Cannot delete the system default currency ({default_currency})'
            }, 400
        
        try:
            db.session.delete(currency)
            db.session.commit()
            return {'status': 'success', 'message': f'Currency {code} deleted'}, 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting currency: {str(e)}")
            return {'status': 'error', 'message': 'Could not delete currency'}, 500

# User Currency endpoints
@ns.route('/user/currencies')
class UserCurrencyList(Resource):
    @ns.marshal_list_with(user_currency_detail_model)
    @ns.response(200, 'Success')
    @jwt_required()
    def get(self):
        """Get currencies assigned to the current user."""
        user_id = get_jwt_identity()
        
        # Get the user currencies with joined currency data
        from sqlalchemy.orm import joinedload
        user_currencies = UserCurrency.query.filter_by(user_id=user_id).options(
            joinedload(UserCurrency.currency)
        ).all()
        
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
        
        # Get the currency code
        currency_code = data.get('currency_code')
        if not currency_code:
            return {'status': 'error', 'message': 'currency_code is required'}, 400
        
        # Check if currency exists and is active
        currency = Currency.query.get(currency_code)
        if not currency:
            return {'status': 'error', 'message': f'Currency {currency_code} not found'}, 404
        
        if not currency.is_active:
            return {'status': 'error', 'message': f'Currency {currency_code} is not active'}, 400
        
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
        
        # Create the assignment
        new_assignment = UserCurrency(
            user_id=user_id,
            currency_code=currency_code,
            is_default=data.get('is_default', False)
        )
        
        # If setting as default, unset any existing default
        if new_assignment.is_default:
            UserCurrency.query.filter_by(
                user_id=user_id,
                is_default=True
            ).update({'is_default': False})
        
        try:
            db.session.add(new_assignment)
            db.session.commit()
            return new_assignment, 201
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error assigning currency: {str(e)}")
            return {'status': 'error', 'message': 'Could not assign currency'}, 500

@ns.route('/user/currencies/<string:currency_code>')
class UserCurrencyDetail(Resource):
    @ns.marshal_with(user_currency_detail_model)
    @ns.response(200, 'Success')
    @ns.response(404, 'User currency assignment not found')
    @jwt_required()
    def get(self, currency_code):
        """Get details of a specific currency assignment for current user."""
        user_id = get_jwt_identity()
        
        from sqlalchemy.orm import joinedload
        user_currency = UserCurrency.query.filter_by(
            user_id=user_id,
            currency_code=currency_code
        ).options(
            joinedload(UserCurrency.currency)
        ).first_or_404()
        
        return user_currency
    
    @ns.expect(ns.model('UpdateUserCurrency', {
        'is_default': fields.Boolean(description='Set as default currency')
    }))
    @ns.marshal_with(user_currency_detail_model)
    @ns.response(200, 'User currency updated')
    @jwt_required()
    def put(self, currency_code):
        """Update currency assignment settings."""
        user_id = get_jwt_identity()
        data = request.json
        
        # Get the assignment
        from sqlalchemy.orm import joinedload
        user_currency = UserCurrency.query.filter_by(
            user_id=user_id,
            currency_code=currency_code
        ).options(
            joinedload(UserCurrency.currency)
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
        
        try:
            db.session.commit()
            return user_currency, 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating user currency: {str(e)}")
            return {'status': 'error', 'message': 'Could not update currency settings'}, 500
    
    @ns.response(200, 'Currency assignment removed')
    @ns.response(400, 'Cannot remove default currency')
    @jwt_required()
    def delete(self, currency_code):
        """Remove a currency assignment from current user."""
        user_id = get_jwt_identity()
        
        # Get the assignment
        user_currency = UserCurrency.query.filter_by(
            user_id=user_id,
            currency_code=currency_code
        ).first_or_404()
        
        # Don't allow removing the default currency
        if user_currency.is_default:
            return {
                'status': 'error',
                'message': 'Cannot remove your default currency. Set another currency as default first.'
            }, 400
        
        # Don't allow removing if it's the user's only currency
        count = UserCurrency.query.filter_by(user_id=user_id).count()
        if count <= 1:
            return {
                'status': 'error',
                'message': 'Cannot remove your only currency assignment.'
            }, 400
        
        try:
            db.session.delete(user_currency)
            db.session.commit()
            return {'status': 'success', 'message': f'Currency {currency_code} removed from your account'}, 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error removing user currency: {str(e)}")
            return {'status': 'error', 'message': 'Could not remove currency assignment'}, 500

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
        """Set a user's default currency from their assigned currencies."""
        user_id = get_jwt_identity()
        data = request.json
        
        # Get the currency code
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
        
        try:
            # Unset current default
            UserCurrency.query.filter_by(
                user_id=user_id,
                is_default=True
            ).update({'is_default': False})
            
            # Set new default
            user_currency.is_default = True
            db.session.commit()
            
            # Store in session for current request
            from flask import session
            session['currency'] = currency_code
            
            return {
                'status': 'success',
                'message': f'Default currency set to {currency_code}'
            }, 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error setting default currency: {str(e)}")
            return {'status': 'error', 'message': 'Could not update default currency'}, 500

# Admin endpoints for managing user currencies
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
        user = User.query.get_or_404(user_id)
        
        # Get user currencies with joined currency data
        from sqlalchemy.orm import joinedload
        user_currencies = UserCurrency.query.filter_by(user_id=user_id).options(
            joinedload(UserCurrency.currency)
        ).all()
        
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
        
        # Create the assignment
        new_assignment = UserCurrency(
            user_id=user_id,
            currency_code=currency_code,
            is_default=data.get('is_default', False)
        )
        
        # If setting as default, unset any existing default
        if new_assignment.is_default:
            UserCurrency.query.filter_by(
                user_id=user_id,
                is_default=True
            ).update({'is_default': False})
        
        try:
            db.session.add(new_assignment)
            db.session.commit()
            return new_assignment, 201
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error assigning currency to user: {str(e)}")
            return {'status': 'error', 'message': 'Could not assign currency'}, 500