from flask import Flask
import os
from dotenv import load_dotenv

def create_app():
    """Create and configure the Flask application."""
    load_dotenv()
    print("hello")
    app = Flask(__name__, template_folder='templates')
    app.secret_key = os.getenv("SECRET_KEY")

    from .routes.map_display import map_display_bp
    app.register_blueprint(map_display_bp)
    
    return app