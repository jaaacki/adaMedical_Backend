
from app.extensions import db
from flask import Flask
from main import create_app

app = create_app()

with app.app_context():
    # Drop alembic_version table
    db.engine.execute("DROP TABLE IF EXISTS alembic_version")
    print("alembic_version table dropped successfully")