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

app = Flask(__name__)

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


@app.post("/api/bureaucracy")
def run_bureaucracy():
    state = request.get_json() or {}
    bureaucracy(state)
    return jsonify({"error_code": ErrorCode.E_OK.value})

# -------------------------------------------------------------------------------------------------
# Main

if __name__ == "__main__":
    app.run(port=8000, debug=True)
