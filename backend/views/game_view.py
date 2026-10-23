# -------------------------------------------------------------------------------------------------
# Imports

from backend.data.files import (
    load_map,
    load_money,
    load_plant_deck,
    load_replenishment,
    load_resources,
    load_settings,
)
from backend.rules.common.game_state import GameState
from backend.rules.common.phase_state import phase_key
from backend.views.map_view import build_map_view
from backend.views.market_view import (
    money_view,
    next_card_back_view,
    power_plant_market_view,
    replenishment_view,
    resource_market_view,
)
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

def header_view(config, state: GameState):
    """Describe the header: the turn order and what the current player is doing."""
    current = state.current_player
    phase = phase_key(state.current_action)
    finished_players = state.phase_finished_players.get(phase, [])
    turn_order = []

    for player in state.player_turn_order:
        classes = ["turn-order-player"]

        if player == current:
            classes.append("current")

        if player in finished_players:
            classes.append("finished")

        turn_order.append({
            "label": player_label(state, player),
            "color": player_color(config, state, player),
            "current": player == current,
            "finished": player in finished_players,
            "classes": classes,
        })

    action = state.current_action
    action_label = config["text"]["action_labels"].get(action, action)

    return {
        "turn_order": turn_order,
        "placement_status": f"{action_label} · {player_label(state, current)}",
        "cycles": state.cycles,
    }

# -------------------------------------------------------------------------------------------------
# Whole page

def build_view(state: GameState):
    """Describe everything the UI shows, built from the game state and the static JSON files."""
    config = load_config()
    deck = load_plant_deck()

    # The board shows players in a fixed roster order, which never changes with the turn order.
    board_order = list(state.player_colors or state.player_aliases)

    players = {}

    for player in board_order:
        players[player] = {
            "label": player_label(state, player),
            "color": player_color(config, state, player),
        }

    selected_spots = set()

    for house in state.pending_houses:
        selected_spots.add((house["city"], house["spot"]))

    player_rows = []

    for player in board_order[:config["rules"]["max_players_on_board"]]:
        player_rows.append(player_row(config, state, player, deck))

    return {
        "map": build_map_view(config, load_map(), state.map_houses, players, selected_spots),
        "header": header_view(config, state),
        "players": player_rows,
        "power_plant_market": power_plant_market_view(config, state, deck),
        "resource_market": resource_market_view(config, state),
        "next_card_back": next_card_back_view(config, state, deck),
        "money": money_view(load_money()),
        "replenishment": replenishment_view(config, state, load_replenishment()),
    }
