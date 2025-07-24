from flask import Flask
import os
from dotenv import load_dotenv

def create_app():
    """Create and configure the Flask application."""
    load_dotenv()  
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")

    from .routes.map_display import map_display_bp
    app.register_blueprint(map_display_bp)
    

    return app