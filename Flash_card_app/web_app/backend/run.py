import os
from pathlib import Path

from flask import Flask
from flask_cors import CORS
from app.config import Config
from app.models import db
from app.routes import api


FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"


def create_app():
    """Application factory"""
    app = Flask(
        __name__,
        static_folder=str(FRONTEND_DIR),
        static_url_path="",
    )
    app.config.from_object(Config)
    
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    @app.route("/")
    def index():
        return app.send_static_file("index.html")

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


app = create_app()


if __name__ == "__main__":
    app.run(
        debug=False,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
    )
