# -------------------------------------------------------------------------------------------------
# Imports

from backend.data_files import (
    load_map,
    load_money,
    load_plant_deck,
    load_replenishment,
    load_resources,
    load_settings,
)
from backend.views.map_view import build_map_view
from backend.views.market_view import money_view, replenishment_view, resource_market_view
from backend.views.plant_view import plant_card
from backend.views.player_view import player_color, player_label, player_row

# -------------------------------------------------------------------------------------------------
# Configuration

def load_config():
    """Return the rules, texts, colors, price scales and resources that define the game."""
    settings = load_settings()
    resources = load_resources()

    return {
        "rules": settings["rules"],
        "text": settings["text"],
        "display": settings["display"],
        "price_scales": resources["price_scales"],
        "resources": resources["resources"],
    }

# -------------------------------------------------------------------------------------------------
# Header

def header_view(config, state):
    """Describe the header: the turn order and what the current player is doing."""
    current = state["current_player"]
    turn_order = []

    for player in state["player_turn_order"]:
        classes = ["turn-order-player"]

        if player == current:
            classes.append("current")

        turn_order.append({
            "label": player_label(state, player),
            "color": player_color(config, state, player),
            "current": player == current,
            "classes": classes,
        })

    action = state["current_action"]
    action_label = config["text"]["action_labels"].get(action, action)

    return {
        "turn_order": turn_order,
        "placement_status": f"{action_label} · {player_label(state, current)}",
    }

# -------------------------------------------------------------------------------------------------
# Next card back

def next_card_back_view(config, state):
    """Describe the back of the next power plant card: its heading, its label and its back type."""
    back = state["back_of_the_next_card"]
    text = config["text"]

    return {
        "heading": text["next_card_heading"],
        "classes": ["info-card", "next-card-back", back],
        "label": text["back_of_the_card"][back],
    }

# -------------------------------------------------------------------------------------------------
# Whole page

def build_view(state):
    """Describe everything the UI shows, built from the game state and the static JSON files."""
    config = load_config()
    deck = load_plant_deck()

    players = {}
    for player in state["player_turn_order"]:
        players[player] = {"label": player_label(state, player), "color": player_color(config, state, player)}

    selected = set()
    for house in state["pending_houses"]:
        selected.add((house["city"], house["spot"]))

    player_rows = []
    for player in state["player_turn_order"][:config["rules"]["max_players_on_board"]]:
        player_rows.append(player_row(config, state, player, deck))

    market_cards = []
    for plant_id in state["power_plant_market"]:
        market_cards.append(plant_card(config, plant_id, deck.get(plant_id), False))

    return {
        "map": build_map_view(config, load_map(), state["map_houses"], players, selected),
        "header": header_view(config, state),
        "players": player_rows,
        "power_plant_market": market_cards,
        "resource_market": resource_market_view(config, state),
        "next_card_back": next_card_back_view(config, state),
        "money": money_view(load_money()),
        "replenishment": replenishment_view(config, state, load_replenishment()),
    }
