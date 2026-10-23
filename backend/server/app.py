# -------------------------------------------------------------------------------------------------
# Imports

from flask import Flask

from backend.server.routes import routes

# -------------------------------------------------------------------------------------------------
# App factory

def create_app(game_service):
    """Create a Flask app that serves the given game service."""
    app = Flask(__name__)
    app.config["game_service"] = game_service
    app.register_blueprint(routes)

    return app
