# -------------------------------------------------------------------------------------------------
# Imports

from flask import Flask

from backend.server.routes import routes

# -------------------------------------------------------------------------------------------------
# App factory

def create_app(game_service=None, load_state=None, save_state=None, plant_slots_per_player=3):
    """Create the app shell; a game service is installed after new or load is chosen."""
    app = Flask(__name__)
    app.config["game_service"] = game_service
    app.config["load_state"] = load_state
    app.config["save_state"] = save_state
    app.config["plant_slots_per_player"] = plant_slots_per_player
    app.register_blueprint(routes)

    return app
