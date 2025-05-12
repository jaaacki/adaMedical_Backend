# app/core/repository.py
from app.extensions import db
from sqlalchemy.exc import SQLAlchemyError

class BaseRepository:
    """Base repository for database operations."""
    
    model_class = None
    
    def __init__(self, model_class=None):
        if model_class:
            self.model_class = model_class
    
    def get_by_id(self, id):
        """Get a record by ID."""
        return self.model_class.query.get(id)
    
    def get_by_field(self, field, value):
        """Get a record by specific field."""
        return self.model_class.query.filter(getattr(self.model_class, field) == value).first()
    
    def list(self, **filters):
        """List all records with optional filters."""
        query = self.model_class.query
        for field, value in filters.items():
            if hasattr(self.model_class, field) and value is not None:
                query = query.filter(getattr(self.model_class, field) == value)
        return query.all()
    
    def create(self, **kwargs):
        """Create a new record."""
        instance = self.model_class(**kwargs)
        db.session.add(instance)
        try:
            db.session.commit()
            return instance
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    def update(self, instance, **kwargs):
        """Update an existing record."""
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        try:
            db.session.commit()
            return instance
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    def delete(self, instance):
        """Delete a record."""
        db.session.delete(instance)
        try:
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e