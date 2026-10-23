# -------------------------------------------------------------------------------------------------
# Imports

from flask import Blueprint, abort, current_app, jsonify, redirect, send_from_directory

from backend.data.files import PROJECT_ROOT, load_settings
from backend.rules.common.error_codes import ErrorCode
from backend.server.messages import (
    BID_PLACED,
    GAME_SAVED,
    HOUSE_SPOT_NOT_AVAILABLE,
    HOUSE_SPOT_UPDATED,
    INVALID_POWER_PLANT,
    INVALID_RESOURCE_MOVE,
    PASSED,
    PLACEHOLDER_BUREAUCRACY,
    PLACEHOLDER_HOUSE_PURCHASE,
    PLACEHOLDER_RESOURCE_PRICE,
    PLACEHOLDER_RESOURCE_PURCHASE,
    POWER_PLANT_DISCARDED,
    POWER_PLANT_READY_UPDATED,
    POWER_PLANT_SELECTED,
    RESOURCE_MOVE_REJECTED,
    RESOURCE_MOVED,
)
from backend.server.request_helpers import build_reply, get_payload, has_int, has_text
from backend.views.game_view import build_view

# -------------------------------------------------------------------------------------------------
# Constants

# Only these folders of the project are served to the browser.
PUBLIC_DIRECTORIES = ["ui", "game_info"]

routes = Blueprint("routes", __name__)


def game_service():
    """Return the game service the app was created with."""
    return current_app.config["game_service"]

# -------------------------------------------------------------------------------------------------
# Pages and view

@routes.get("/")
def index():
    """Redirect the site root to the map page."""
    return redirect("/ui/map.html")


@routes.get("/api/view")
def view():
    """Return everything the UI shows, built from the game state."""
    return jsonify(build_view(game_service().snapshot()))


@routes.get("/<path:filename>")
def serve_file(filename):
    """Serve a file from the ui or game_info folder; anything else is a 404."""
    directory, _, relative_path = filename.partition("/")

    if directory not in PUBLIC_DIRECTORIES:
        abort(404)

    return send_from_directory(PROJECT_ROOT / directory, relative_path)


@routes.post("/api/save-game")
def save_game():
    """Save the current game state to the save game file."""
    game_service().save_game()

    return build_reply(ErrorCode.E_OK, GAME_SAVED)

# -------------------------------------------------------------------------------------------------
# Phase two: auction

@routes.post("/api/plant/select")
def select_plant():
    """Select a power plant from the market."""
    payload = get_payload()

    if not has_int(payload, ["plant_id"]):
        return build_reply(ErrorCode.E_NOT_OKAY, INVALID_POWER_PLANT)

    code = game_service().select_power_plant(payload["plant_id"])

    if code != ErrorCode.E_OK:
        return build_reply(code, INVALID_POWER_PLANT)

    return build_reply(code, POWER_PLANT_SELECTED)


@routes.post("/api/bid")
def bid():
    """Place a bid in the power plant auction."""
    payload = get_payload()

    if not has_int(payload, ["amount"]):
        return build_reply(ErrorCode.E_NOT_OKAY, BID_PLACED)

    code = game_service().place_bid(payload.get("player"), payload["amount"])

    return build_reply(code, BID_PLACED)


@routes.post("/api/bid/pass")
def pass_bid():
    """Pass in the power plant auction."""
    code = game_service().pass_bid(get_payload().get("player"))

    return build_reply(code, PASSED)


@routes.post("/api/plant/discard")
def discard_plant():
    """Discard an owned plant to make room for the plant that was just bought."""
    payload = get_payload()

    if not has_text(payload, ["player"]) or not has_int(payload, ["plant_id"]):
        return build_reply(ErrorCode.E_NOT_OKAY, INVALID_POWER_PLANT)

    code = game_service().discard_power_plant(payload["player"], payload["plant_id"])

    if code != ErrorCode.E_OK:
        return build_reply(code, INVALID_POWER_PLANT)

    return build_reply(code, POWER_PLANT_DISCARDED)

# -------------------------------------------------------------------------------------------------
# Phase three: resources

@routes.post("/api/resource-price")
def resource_price():
    """Return the price of the resources typed in the buy panel."""
    payload = get_payload()
    price = game_service().quote_resources(payload.get("player"), payload.get("resources"))
    price_label = load_settings()["text"]["price_format"].format(price=price)

    return build_reply(ErrorCode.E_OK, PLACEHOLDER_RESOURCE_PRICE, price_label)


@routes.post("/api/buy-resources")
def buy_resources():
    """Buy the resources typed in the buy panel."""
    payload = get_payload()
    code = game_service().buy_resources(payload.get("player"), payload.get("resources"))

    return build_reply(code, PLACEHOLDER_RESOURCE_PURCHASE)

# -------------------------------------------------------------------------------------------------
# Phase four: houses

@routes.post("/api/house-spot")
def house_spot():
    """Select or deselect a free house spot."""
    payload = get_payload()

    if not has_text(payload, ["city", "spot"]):
        return build_reply(ErrorCode.E_NOT_OKAY, HOUSE_SPOT_NOT_AVAILABLE)

    code = game_service().toggle_house_spot(payload["city"], payload["spot"])

    if code != ErrorCode.E_OK:
        return build_reply(code, HOUSE_SPOT_NOT_AVAILABLE)

    return build_reply(code, HOUSE_SPOT_UPDATED)


@routes.post("/api/buy-houses")
def buy_houses():
    """Buy the selected houses for the current player."""
    code = game_service().buy_houses(get_payload().get("player"))

    return build_reply(code, PLACEHOLDER_HOUSE_PURCHASE)

# -------------------------------------------------------------------------------------------------
# Phase five: bureaucracy

@routes.post("/api/plant/ready-to-power")
def ready_to_power():
    """Flip the ready-to-power flag of a plant."""
    payload = get_payload()

    if not has_text(payload, ["player"]) or not has_int(payload, ["plant_id"]):
        return build_reply(ErrorCode.E_NOT_OKAY, INVALID_POWER_PLANT)

    code = game_service().toggle_ready_to_power(payload["player"], payload["plant_id"])

    if code != ErrorCode.E_OK:
        return build_reply(code, INVALID_POWER_PLANT)

    return build_reply(code, POWER_PLANT_READY_UPDATED)


@routes.post("/api/bureaucracy")
def bureaucracy():
    """Finish the bureaucracy turn of the current player."""
    code = game_service().bureaucracy(get_payload().get("player"))

    return build_reply(code, PLACEHOLDER_BUREAUCRACY)

# -------------------------------------------------------------------------------------------------
# Any phase

@routes.post("/api/transfer-plant-resource")
def transfer_plant_resource():
    """Move one fuel unit between two plants of a player."""
    payload = get_payload()
    int_names = ["source_plant_id", "source_slot", "target_plant_id", "target_slot"]

    if not has_text(payload, ["player"]) or not has_int(payload, int_names):
        return build_reply(ErrorCode.E_NOT_OKAY, INVALID_RESOURCE_MOVE)

    code = game_service().transfer_resource(
        payload["player"],
        payload["source_plant_id"],
        payload["source_slot"],
        payload["target_plant_id"],
        payload["target_slot"],
    )

    if code != ErrorCode.E_OK:
        return build_reply(code, RESOURCE_MOVE_REJECTED)

    return build_reply(code, RESOURCE_MOVED)
