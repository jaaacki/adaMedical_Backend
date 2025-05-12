#!/usr/bin/env python3
"""
Enhanced debug script to test MySQL connection with mysqlclient.
"""

import sys
import os
import importlib

# Print Python environment information
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")

# Check MySQLdb
try:
    print("\nChecking MySQLdb...")
    import MySQLdb
    print(f"✅ MySQLdb imported successfully - version: {getattr(MySQLdb, '__version__', 'unknown')}")
    print(f"   Location: {MySQLdb.__file__}")
    
    # Try directly using MySQLdb to verify it can connect
    try:
        conn = MySQLdb.connect(
            host='db',
            user='user',
            passwd='password',
            db='appdb'
        )
        print("✅ Direct MySQLdb connection successful!")
        conn.close()
    except Exception as e:
        print(f"❌ Direct MySQLdb connection failed: {e}")
except ImportError as e:
    print(f"❌ Error importing MySQLdb: {e}")

# Check SQLAlchemy dialects
try:
    print("\nChecking SQLAlchemy...")
    import sqlalchemy
    print(f"✅ SQLAlchemy imported successfully - version: {sqlalchemy.__version__}")
    print(f"   Location: {sqlalchemy.__file__}")
    
    # Check if the dialect package exists
    dialect_path = os.path.join(os.path.dirname(sqlalchemy.__file__), 'dialects', 'mysql')
    print(f"\nChecking dialect path: {dialect_path}")
    if os.path.exists(dialect_path):
        print(f"✅ Dialect directory exists")
        print("Files in dialect directory:")
        for f in os.listdir(dialect_path):
            print(f"   - {f}")
    else:
        print(f"❌ Dialect directory does not exist")
    
    # Try importing the dialect module directly
    try:
        print("\nAttempting to import MySQL dialect directly...")
        from sqlalchemy.dialects.mysql.mysqldb import MySQLDialect_mysqldb
        print(f"✅ MySQL dialect module imported successfully")
    except ImportError as e:
        print(f"❌ Error importing MySQL dialect module: {e}")
    
    # Check SQLAlchemy's dialect registry
    print("\nChecking SQLAlchemy dialect registry...")
    from sqlalchemy.dialects import registry
    
    print("Available dialects:")
    for name in dir(registry):
        if not name.startswith('_'):
            print(f"   - {name}")
    
    # Try creating an engine directly
    try:
        print("\nTrying to create SQLAlchemy engine with explicit dialect...")
        from sqlalchemy import create_engine
        
        # Try with pymysql as fallback
        try:
            import pymysql
            print(f"PyMySQL is available (version: {pymysql.__version__})")
            engine_pymysql = create_engine("mysql+pymysql://user:password@db:3306/appdb")
            print("✅ Engine with pymysql created successfully")
        except ImportError:
            print("PyMySQL is not available")
        
        # Try with mysqlclient
        engine_mysqlclient = create_engine("mysql+mysqldb://user:password@db:3306/appdb")
        print("✅ Engine with mysqldb created successfully")
        
    except Exception as e:
        print(f"❌ Error creating engine: {e}")
        
except ImportError as e:
    print(f"❌ Error importing sqlalchemy: {e}")

print("\nDebug complete - Please send this output to troubleshoot your MySQL issue")