# app/currencies/models.py
from app.extensions import db
import datetime

class Currency(db.Model):
    """Model for available currencies in the system."""
    __tablename__ = 'currencies'
    
    code = db.Column(db.String(3), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    symbol = db.Column(db.String(5), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    user_currencies = db.relationship('UserCurrency', back_populates='currency', lazy='dynamic')
    
    def __repr__(self):
        return f'<Currency {self.code}>'
    
    @classmethod
    def get_default(cls):
        """Get the system default currency (SGD)."""
        from flask import current_app
        default_code = current_app.config.get('DEFAULT_CURRENCY', 'SGD')
        return cls.query.get(default_code) or cls.query.first()


class UserCurrency(db.Model):
    """Model for user currency assignments."""
    __tablename__ = 'user_currencies'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    currency_code = db.Column(db.String(3), db.ForeignKey('currencies.code', ondelete='CASCADE'), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='currencies')
    currency = db.relationship('Currency', back_populates='user_currencies')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'currency_code', name='uq_user_currency'),
    )
    
    def __repr__(self):
        return f'<UserCurrency user_id={self.user_id} currency={self.currency_code}>'
    
    @classmethod
    def set_default(cls, user_id, currency_code):
        """Set a currency as the default for a user, unset any existing default."""
        # Unset any existing default
        cls.query.filter_by(user_id=user_id, is_default=True).update({'is_default': False})
        db.session.flush()
        
        # Set the new default
        record = cls.query.filter_by(user_id=user_id, currency_code=currency_code).first()
        if record:
            record.is_default = True
            db.session.flush()
            return True
        
        return False