#!/usr/bin/env python3
"""
Reset admin password script with proper Flask application context.
Save as reset_admin.py
"""
from flask import Flask
from app.extensions import db
from app.users.models import User
import os
from main import create_app

# Create the Flask app with application context
app = create_app()

# Use the application context
with app.app_context():
    # Find the admin user
    admin = User.query.filter_by(email='admin@example.com').first()
    
    if admin:
        print(f"Found admin user: {admin.email}")
        # Reset the password
        admin.set_password('AdminPassword123')
        db.session.commit()
        print("Admin password reset successfully")
    else:
        print("Admin user not found")