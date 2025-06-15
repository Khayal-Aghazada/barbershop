from flask_sqlalchemy import SQLAlchemy
import os
import logging

logger = logging.getLogger(__name__)

# Create database instance
db = SQLAlchemy()

def init_db(app):
    """Initialize the database with the app"""
    db.init_app(app)
    
    # Check if database file exists for SQLite
    if 'sqlite:///' in app.config['SQLALCHEMY_DATABASE_URI']:
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if not os.path.exists(db_path):
            logger.info(f"Database file {db_path} does not exist, will be created")
        else:
            logger.info(f"Using existing database file: {db_path}")
    
    # Create tables if they don't exist
    try:
        with app.app_context():
            db.create_all()
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}") 