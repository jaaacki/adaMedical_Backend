"""
Quick script to fix the admin role name through the Flask shell.
Save as fix_admin_role.py and run with: python fix_admin_role.py
"""
from flask import Flask
from app.extensions import db
from app.users.models import Role
from main import create_app

# Create the Flask app with application context
app = create_app()

# Use the application context
with app.app_context():
    # Find the admin role with typo
    admin_role = Role.query.filter(
        (Role.name == 'Admininstrator') | 
        (Role.name == 'Administrator')
    ).first()
    
    if admin_role:
        print(f"Found admin role with name: {admin_role.name}")
        old_name = admin_role.name
        
        # Update the name to the correct spelling
        admin_role.name = 'Admin'
        db.session.commit()
        
        print(f"Updated role name from '{old_name}' to 'Admin'")
        
        # Verify the change
        roles = Role.query.all()
        print("\nCurrent roles in the database:")
        for role in roles:
            print(f"ID: {role.id}, Name: {role.name}")
    else:
        # Check if Admin role already exists
        admin_exists = Role.query.filter_by(name='Admin').first()
        
        if admin_exists:
            print("Role 'Admin' already exists with ID:", admin_exists.id)
        else:
            print("No admin role with typo found. Creating 'Admin' role...")
            
            # Create the Admin role
            admin_role = Role(name='Admin')
            db.session.add(admin_role)
            db.session.commit()
            
            print(f"Created 'Admin' role with ID: {admin_role.id}")
            
    print("\nFixed role check complete!")