#!/usr/bin/env python3
"""
Debug script to help diagnose internal server errors.
"""
import os
import traceback
from flask import Flask

try:
    print("Creating minimal Flask app for debugging...")
    app = Flask(__name__)
    
    # Set up a basic route
    @app.route('/minimal-health')
    def minimal_health():
        return "Debug app is working!"
    
    print("Minimal Flask app configured. Now trying to import the real app...")
    
    # Try importing the main app
    try:
        from main import create_app
        print("Successfully imported create_app from main")
        
        # Try creating the app
        real_app = create_app()
        print("Successfully created the application!")
        
        # Try getting a route
        print("\nTesting routes:")
        
        # Define test route function
        def test_route(path):
            try:
                rule = next((r for r in real_app.url_map.iter_rules() if r.rule == path), None)
                if rule:
                    print(f"✅ Route {path} exists, endpoints: {rule.endpoint}")
                    view_func = real_app.view_functions.get(rule.endpoint)
                    if view_func:
                        print(f"   View function: {view_func.__name__}")
                    else:
                        print(f"❌ View function for {path} not found!")
                else:
                    print(f"❌ Route {path} not found in url_map!")
            except Exception as e:
                print(f"❌ Error testing route {path}: {e}")
        
        # Test critical routes
        test_route('/health')
        test_route('/api/v1/doc/')
        test_route('/api/v1/auth/login')
        
        # Check extensions are initialized
        print("\nChecking extensions:")
        try:
            from app.extensions import db
            print(f"✅ Database extension: {db}")
            
            if not hasattr(db, 'engine') or not db.engine:
                print("❌ Database engine not initialized")
            else:
                print("✅ Database engine initialized")
                
            from app.extensions import jwt
            print(f"✅ JWT extension: {jwt}")
            
        except Exception as e:
            print(f"❌ Error checking extensions: {e}")
        
        # Print all registered routes
        print("\nAll registered routes:")
        for rule in sorted(real_app.url_map.iter_rules(), key=lambda x: str(x)):
            print(f"  {rule.rule} -> {rule.endpoint}")
        
    except ImportError as e:
        print(f"❌ Failed to import create_app: {e}")
        traceback.print_exc()
    except Exception as e:
        print(f"❌ Error creating application: {e}")
        traceback.print_exc()
    
    print("\nDebug complete")
    
except Exception as e:
    print(f"❌ Critical error in debug script: {e}")
    traceback.print_exc()