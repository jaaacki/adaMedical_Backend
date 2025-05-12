#!/usr/bin/env python3
"""
Quick script to fix SQLAlchemy MySQL connectivity by forcing PyMySQL.
Add this file to your project and import it in your application before initializing SQLAlchemy.
"""

import pymysql
import warnings

# Register PyMySQL as an alternative implementation of MySQLdb
print("Registering PyMySQL as a MySQL handler...")
pymysql.install_as_MySQLdb()

# Suppress warnings about using PyMySQL with SQLAlchemy
warnings.filterwarnings("ignore", message=".*PyMySQL.*")

print("PyMySQL registered as MySQLdb successfully!")