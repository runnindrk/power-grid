# -------------------------------------------------------------------------------------------------
# Imports

from pathlib import Path
import sys

from flask import Flask, jsonify, redirect, request, send_from_directory

# -------------------------------------------------------------------------------------------------
# Constants

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.rules.rules import ErrorCode, bureaucracy, build_houses, buy_resources
from backend.server.game_state_store import GAME_STATE_PATH
from backend.server.resource_transfer_service import PLANT_DECK_PATH, transfer_resource

app = Flask(__name__)
app.config.update(
    GAME_STATE_PATH=GAME_STATE_PATH,
    PLANT_DECK_PATH=PLANT_DECK_PATH,
)

# -------------------------------------------------------------------------------------------------
# Routes

@app.route("/")
def index():
    return redirect("/ui/map.html")


@app.route("/<path:filename>")
def serve_file(filename):
    return send_from_directory(PROJECT_ROOT, filename)


@app.post("/api/house-price")
def house_price():
    payload = request.get_json() or {}
    price, result = build_houses(payload.get("player"), payload.get("houses", []))
    if result != ErrorCode.E_OK:
        return jsonify({"error_code": result.value}), 400
    return jsonify({"price": price, "error_code": result.value})


@app.post("/api/buy-houses")
def buy_houses():
    payload = request.get_json() or {}
    price, result = build_houses(payload.get("player"), payload.get("houses", []))
    if result != ErrorCode.E_OK:
        return jsonify({"error_code": result.value}), 400
    return jsonify({"price": price, "error_code": result.value})


@app.post("/api/resource-price")
def resource_price():
    payload = request.get_json() or {}
    price, result = buy_resources(payload.get("player"), payload.get("resources", {}))
    if result != ErrorCode.E_OK:
        return jsonify({"error_code": result.value}), 400
    return jsonify({"price": price, "error_code": result.value})


@app.post("/api/buy-resources")
def buy_resources_for_player():
    payload = request.get_json() or {}
    price, result = buy_resources(payload.get("player"), payload.get("resources", {}))
    if result != ErrorCode.E_OK:
        return jsonify({"error_code": result.value}), 400
    return jsonify({"price": price, "error_code": result.value})


@app.post("/api/transfer-plant-resource")
def transfer_plant_resource():
    payload = request.get_json(silent=True)
    required_strings = ("player",)
    required_integers = (
        "source_plant_id",
        "source_slot",
        "target_plant_id",
        "target_slot",
    )
    if (
        not isinstance(payload, dict)
        or any(not isinstance(payload.get(key), str) for key in required_strings)
        or any(
            not isinstance(payload.get(key), int) or isinstance(payload.get(key), bool)
            for key in required_integers
        )
    ):
        return jsonify({"error_code": ErrorCode.E_NOT_OKAY.value}), 400

    state, result = transfer_resource(
        payload["player"],
        payload["source_plant_id"],
        payload["source_slot"],
        payload["target_plant_id"],
        payload["target_slot"],
        Path(app.config["GAME_STATE_PATH"]),
        Path(app.config["PLANT_DECK_PATH"]),
    )
    if result != ErrorCode.E_OK:
        return jsonify({"error_code": result.value}), 409
    return jsonify({"game_state": state, "error_code": result.value})


@app.post("/api/bureaucracy")
def run_bureaucracy():
    state = request.get_json() or {}
    bureaucracy(state)
    return jsonify({"error_code": ErrorCode.E_OK.value})

# -------------------------------------------------------------------------------------------------
# Main

if __name__ == "__main__":
    app.run(port=8000, debug=True)
