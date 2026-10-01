# -------------------------------------------------------------------------------------------------
# Imports

from pathlib import Path
import json
import sys

from flask import Flask, jsonify, redirect, request, send_from_directory

# -------------------------------------------------------------------------------------------------
# Constants

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GAME_STATE_PATH = PROJECT_ROOT / "game_info" / "game_state" / "power_grid_game_state.json"
sys.path.insert(0, str(PROJECT_ROOT))

from backend.rules.rules import ErrorCode, build_house

app = Flask(__name__)

# -------------------------------------------------------------------------------------------------
# Routes

@app.route("/")
def index():
    return redirect("/ui/map.html")


@app.route("/<path:filename>")
def serve_file(filename):
    return send_from_directory(PROJECT_ROOT, filename)


@app.post("/api/place-house")
def place_house():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Expected a JSON request body"}), 400

    player = payload.get("player")
    city = payload.get("city")
    spot = payload.get("spot")
    if not all(isinstance(value, str) for value in (player, city, spot)):
        return jsonify({"error": "player, city, and spot are required"}), 400

    with GAME_STATE_PATH.open(encoding="utf-8") as state_file:
        state = json.load(state_file)

    houses = state.get("map_houses", {})
    if city not in houses or spot not in houses[city]:
        return jsonify({"error": "Unknown city or house spot"}), 400

    result = build_house(player, city, houses)
    if result != ErrorCode.E_OK:
        return jsonify({"error": result}), 400

    city_houses = houses[city]
    city_houses[spot] = None if city_houses[spot] == player else player
    with GAME_STATE_PATH.open("w", encoding="utf-8") as state_file:
        json.dump(state, state_file, ensure_ascii=False, indent=4)
        state_file.write("\n")

    return jsonify(state)

# -------------------------------------------------------------------------------------------------
# Main

if __name__ == "__main__":
    app.run(port=8000, debug=True)
