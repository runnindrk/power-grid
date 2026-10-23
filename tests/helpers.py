# -------------------------------------------------------------------------------------------------
# Imports

from backend.application.game_service import GameService
from backend.data.game_state_store import load_game_state
from backend.rules.common.constants import POWER_PLANT_AUCTION
from backend.server.app import create_app

# -------------------------------------------------------------------------------------------------
# Shared test setup

def new_auction_state():
    """Return a fresh copy of the save game, placed at the start of the power plant auction."""
    state = load_game_state()
    state.phase = 2
    state.current_action = POWER_PLANT_AUCTION
    state.current_player = state.player_turn_order[0]

    return state


def new_service(state, rng=None):
    """Return a game service for the state that does not write the save game."""
    return GameService(state, lambda saved: None, rng=rng)


def new_client(state):
    """Return a Flask test client that serves a new game service around the state."""
    return create_app(new_service(state)).test_client()


def find_by_label(rows, label):
    """Return the row of a view list (turn order, players) with the given label."""
    for row in rows:
        if row["label"] == label:
            return row

    return None
