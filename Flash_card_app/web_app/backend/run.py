from flask import Flask
from flask_cors import CORS
from app.config import Config
from app.models import db
from app.routes import api


def create_app():
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize database
    db.init_app(app)
    
    # Enable CORS for all routes
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(api)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
