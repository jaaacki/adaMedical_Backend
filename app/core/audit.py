# app/core/audit.py
from app.extensions import db
from flask import g
import datetime
import json

class AuditLog(db.Model):
    """Model for storing audit logs."""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(64), nullable=False, index=True)
    entity_id = db.Column(db.Integer, nullable=False, index=True)
    action = db.Column(db.String(16), nullable=False, index=True)  # create, update, delete
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    data = db.Column(db.Text, nullable=True)  # JSON string of changes
    
    def __repr__(self):
        return f'<AuditLog {self.action} {self.entity_type}:{self.entity_id}>'

def log_change(entity_type, entity_id, action, changes=None):
    """Log a change to an entity."""
    user_id = getattr(g, 'user_id', None)
    
    audit_log = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        user_id=user_id,
        data=json.dumps(changes) if changes else None
    )
    
    db.session.add(audit_log)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error saving audit log: {e}")

class AuditableMixin:
    """Mixin to add audit logging to models."""
    
    @staticmethod
    def _get_changes(old_dict, new_dict):
        """Calculate changes between old and new dictionaries."""
        changes = {}
        for key, value in new_dict.items():
            if key in old_dict and old_dict[key] != value:
                changes[key] = {
                    'old': old_dict[key],
                    'new': value
                }
        return changes
    
    def _to_dict(self):
        """Convert model to dictionary for audit comparison."""
        result = {}
        for column in self.__table__.columns:
            result[column.name] = getattr(self, column.name)
        return result
    
    def log_create(self):
        """Log creation of an entity."""
        log_change(
            entity_type=self.__tablename__,
            entity_id=self.id,
            action='create',
            changes=self._to_dict()
        )
    
    def log_update(self, old_dict):
        """Log update of an entity."""
        new_dict = self._to_dict()
        changes = self._get_changes(old_dict, new_dict)
        if changes:
            log_change(
                entity_type=self.__tablename__,
                entity_id=self.id,
                action='update',
                changes=changes
            )
    
    def log_delete(self):
        """Log deletion of an entity."""
        log_change(
            entity_type=self.__tablename__,
            entity_id=self.id,
            action='delete',
            changes=self._to_dict()
        )