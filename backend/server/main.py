# -------------------------------------------------------------------------------------------------
# Imports

from pathlib import Path
import sys

from flask import Flask, abort, jsonify, redirect, request, send_from_directory

# -------------------------------------------------------------------------------------------------
# Constants

# Must run before the backend imports so the script works when launched directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.application.game_service import GameService
from backend.data.files import PROJECT_ROOT, load_settings
from backend.data.game_state_store import load_game_state, save_game_state
from backend.rules.common.error_codes import ErrorCode
from backend.server.messages import (
    GAME_SAVED,
    HOUSE_SPOT_NOT_AVAILABLE,
    HOUSE_SPOT_UPDATED,
    INVALID_POWER_PLANT,
    INVALID_RESOURCE_MOVE,
    PLACEHOLDER_BID,
    PLACEHOLDER_BUREAUCRACY,
    PLACEHOLDER_HOUSE_PURCHASE,
    PLACEHOLDER_PASS,
    PLACEHOLDER_RESOURCE_PRICE,
    PLACEHOLDER_RESOURCE_PURCHASE,
    POWER_PLANT_DISCARDED,
    POWER_PLANT_READY_UPDATED,
    POWER_PLANT_SELECTED,
    RESOURCE_MOVE_REJECTED,
    RESOURCE_MOVED,
)
from backend.views.game_view import build_view

PUBLIC_DIRECTORIES = ["ui", "game_info"]

app = Flask(__name__)
app.config["game_service"] = GameService(
    load_game_state(),
    save_game_state,
    load_settings()["rules"]["plant_slots_per_player"],
)


def _game_service():
    return app.config["game_service"]

# -------------------------------------------------------------------------------------------------
# Helpers

def _payload():
    """Return the request JSON object, or an empty dict if it is missing or invalid."""
    payload = request.get_json(silent=True)

    if isinstance(payload, dict):
        return payload
    return {}


def _has_text(payload, names):
    """Return True if every named field of the payload is a string."""
    for name in names:
        if not isinstance(payload.get(name), str):
            return False

    return True


def _has_int(payload, names):
    """Return True if every field is an integer; booleans do not count as integers."""
    for name in names:
        value = payload.get(name)

        if not isinstance(value, int) or isinstance(value, bool):
            return False

    return True


def _result(code, message, price_label=None):
    """Build the JSON reply of an action: error code, status, message and optionally a price."""
    body = {"error_code": code.value, "status": "ok", "message": message}
    status_code = 200

    if code != ErrorCode.E_OK:
        body["status"] = "error"
        body["message"] = message
        status_code = 400

    if price_label is not None:
        body["price_label"] = price_label

    return jsonify(body), status_code

# -------------------------------------------------------------------------------------------------
# Pages and view

@app.route("/")
def index():
    """Redirect the site root to the map page."""
    return redirect("/ui/map.html")


@app.get("/api/view")
def view():
    """Return everything the UI shows, built from the game state."""
    return jsonify(build_view(_game_service().snapshot()))


@app.route("/<path:filename>")
def serve_file(filename):
    """Serve a file from the ui or game_info folder; anything else is a 404."""
    directory, _, relative_path = filename.partition("/")

    if directory not in PUBLIC_DIRECTORIES:
        abort(404)

    return send_from_directory(PROJECT_ROOT / directory, relative_path)


@app.post("/api/save-game")
def save_game():
    """Persist the current in-memory game state as a save game."""
    _game_service().save_game()

    return _result(ErrorCode.E_OK, GAME_SAVED)

# -------------------------------------------------------------------------------------------------
# Actions

@app.post("/api/house-spot")
def house_spot():
    """Select or deselect a free house spot."""
    payload = _payload()

    if not _has_text(payload, ["city", "spot"]):
        return _result(ErrorCode.E_NOT_OKAY, HOUSE_SPOT_NOT_AVAILABLE)

    code = _game_service().toggle_house_spot(payload["city"], payload["spot"])

    if code != ErrorCode.E_OK:
        return _result(code, HOUSE_SPOT_NOT_AVAILABLE)
    return _result(code, HOUSE_SPOT_UPDATED)


@app.post("/api/buy-houses")
def buy_houses_route():
    """Placeholder: buy the selected houses for the current player."""
    code = _game_service().buy_houses(_payload().get("player"))

    return _result(code, PLACEHOLDER_HOUSE_PURCHASE)


@app.post("/api/resource-price")
def resource_price():
    """Placeholder: return the price of the resources typed in the buy panel."""
    payload = _payload()
    price = _game_service().quote_resources(payload.get("player"), payload.get("resources"))
    price_label = load_settings()["text"]["price_format"].format(price=price)

    return _result(ErrorCode.E_OK, PLACEHOLDER_RESOURCE_PRICE, price_label)


@app.post("/api/buy-resources")
def buy_resources_route():
    """Placeholder: buy the resources typed in the buy panel."""
    payload = _payload()
    code = _game_service().buy_resources(payload.get("player"), payload.get("resources"))

    return _result(code, PLACEHOLDER_RESOURCE_PURCHASE)


@app.post("/api/transfer-plant-resource")
def transfer_plant_resource():
    """Move one fuel unit between two plants of a player."""
    payload = _payload()
    int_names = ["source_plant_id", "source_slot", "target_plant_id", "target_slot"]

    if not _has_text(payload, ["player"]) or not _has_int(payload, int_names):
        return _result(ErrorCode.E_NOT_OKAY, INVALID_RESOURCE_MOVE)

    code = _game_service().transfer_resource(
        payload["player"],
        payload["source_plant_id"],
        payload["source_slot"],
        payload["target_plant_id"],
        payload["target_slot"],
    )

    if code != ErrorCode.E_OK:
        return _result(code, RESOURCE_MOVE_REJECTED)
    return _result(code, RESOURCE_MOVED)


@app.post("/api/plant/ready-to-power")
def ready_to_power():
    """Flip the ready-to-power flag of a plant."""
    payload = _payload()

    if not _has_text(payload, ["player"]) or not _has_int(payload, ["plant_id"]):
        return _result(ErrorCode.E_NOT_OKAY, INVALID_POWER_PLANT)

    code = _game_service().toggle_ready_to_power(payload["player"], payload["plant_id"])

    if code != ErrorCode.E_OK:
        return _result(code, INVALID_POWER_PLANT)
    return _result(code, POWER_PLANT_READY_UPDATED)


@app.post("/api/bid")
def bid():
    """Placeholder: place a bid in the power plant auction."""
    payload = _payload()
    if not _has_int(payload, ["amount"]):
        return _result(ErrorCode.E_NOT_OKAY, PLACEHOLDER_BID)

    code = _game_service().place_bid(payload.get("player"), payload.get("amount"))

    return _result(code, PLACEHOLDER_BID)


@app.post("/api/plant/select")
def select_plant():
    """Select a power plant from the market during the auction phase."""
    payload = _payload()

    if not _has_int(payload, ["plant_id"]):
        return _result(ErrorCode.E_NOT_OKAY, INVALID_POWER_PLANT)

    code = _game_service().select_power_plant(payload["plant_id"])

    message = POWER_PLANT_SELECTED if code == ErrorCode.E_OK else INVALID_POWER_PLANT
    return _result(code, message)


@app.post("/api/plant/discard")
def discard_plant():
    """Discard an owned plant to complete a plant purchase replacement."""
    payload = _payload()

    if not _has_text(payload, ["player"]) or not _has_int(payload, ["plant_id"]):
        return _result(ErrorCode.E_NOT_OKAY, INVALID_POWER_PLANT)

    code = _game_service().discard_power_plant(
        payload["player"],
        payload["plant_id"],
    )
    message = POWER_PLANT_DISCARDED if code == ErrorCode.E_OK else INVALID_POWER_PLANT
    return _result(code, message)


@app.post("/api/bid/pass")
def pass_bid_route():
    """Placeholder: pass in the power plant auction."""
    code = _game_service().pass_bid(_payload().get("player"))

    return _result(code, PLACEHOLDER_PASS)


@app.post("/api/bureaucracy")
def run_bureaucracy():
    """Placeholder: run the bureaucracy phase."""
    code = _game_service().bureaucracy(_payload().get("player"))

    return _result(code, PLACEHOLDER_BUREAUCRACY)

# -------------------------------------------------------------------------------------------------
# Main

if __name__ == "__main__":
    app.run(port=8000, debug=True)
