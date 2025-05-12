from app.extensions import db
import datetime

class BaseModel(db.Model):
    """Base model class that other models will inherit from."""
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, 
                          default=datetime.datetime.utcnow, 
                          onupdate=datetime.datetime.utcnow)