# app/core/logging.py
import logging
from logging.handlers import RotatingFileHandler
from flask import request, g, has_request_context
import os
import json

class RequestFormatter(logging.Formatter):
    """Formatter that includes request and user info."""
    
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.method = request.method
            record.remote_addr = request.remote_addr
            if hasattr(g, 'user_id'):
                record.user_id = g.user_id
            else:
                record.user_id = 'unauthenticated'
        else:
            record.url = None
            record.method = None
            record.remote_addr = None
            record.user_id = None
            
        return super().format(record)

def configure_logging(app):
    """Configure application logging."""
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(app.root_path, '..', 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Set up file handler
    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'app.log'),
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = RequestFormatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s [url: %(url)s, user: %(user_id)s]'
    )
    file_handler.setFormatter(file_formatter)
    
    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)
    console_formatter = RequestFormatter(
        '[%(asctime)s] %(levelname)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to the app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.DEBUG if app.debug else logging.INFO)