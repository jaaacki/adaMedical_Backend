# app/extensions.py
"""Module to initialize Flask extensions to avoid circular imports."""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from authlib.integrations.flask_client import OAuth

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
oauth = OAuth()