from flask import Flask

def create_app():
    app = Flask(__name__, template_folder='templates')

    from .routes.map_display import map_display_bp
    app.register_blueprint(map_display_bp)

    from .routes.profile import profile_bp
    app.register_blueprint(profile_bp)
    
    return app