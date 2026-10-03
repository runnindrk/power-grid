# -------------------------------------------------------------------------------------------------
# Imports

from pathlib import Path
import sys

from flask import Flask, abort, jsonify, redirect, request, send_from_directory

# -------------------------------------------------------------------------------------------------
# Constants

# Must run before the backend imports so the script works when launched directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.rules.rules import ErrorCode, bureaucracy, build_houses, buy_resources
from backend.server.paths import PROJECT_ROOT
from backend.server.resource_transfer_service import transfer_resource

PUBLIC_DIRECTORIES = {"ui", "game_info"}

app = Flask(__name__)

# -------------------------------------------------------------------------------------------------
# Routes

@app.route("/")
def index():
    return redirect("/ui/map.html")


@app.route("/<path:filename>")
def serve_file(filename):
    directory, _, relative_path = filename.partition("/")
    if directory not in PUBLIC_DIRECTORIES:
        abort(404)
    return send_from_directory(PROJECT_ROOT / directory, relative_path)


def _priced_response(price, result):
    if result != ErrorCode.E_OK:
        return jsonify({"error_code": result.value}), 400
    return jsonify({"price": price, "error_code": result.value})


@app.post("/api/house-price")
@app.post("/api/buy-houses")
def houses():
    payload = request.get_json() or {}
    return _priced_response(*build_houses(payload.get("player"), payload.get("houses", [])))


@app.post("/api/resource-price")
@app.post("/api/buy-resources")
def resources():
    payload = request.get_json() or {}
    return _priced_response(*buy_resources(payload.get("player"), payload.get("resources", {})))


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


@app.post("/api/transfer-plant-resource")
def transfer_plant_resource():
    payload = request.get_json(silent=True)
    integer_fields = ("source_plant_id", "source_slot", "target_plant_id", "target_slot")
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("player"), str)
        or not all(_is_int(payload.get(key)) for key in integer_fields)
    ):
        return jsonify({"error_code": ErrorCode.E_NOT_OKAY.value}), 400

    state, result = transfer_resource(
        payload["player"],
        payload["source_plant_id"],
        payload["source_slot"],
        payload["target_plant_id"],
        payload["target_slot"],
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
