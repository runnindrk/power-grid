# -------------------------------------------------------------------------------------------------
# Imports

import json

from backend.data.files import GAME_STATE_PATH, load_settings, read_json
from backend.rules.common.game_state import GameState, default_player_colors

# -------------------------------------------------------------------------------------------------
# Game state persistence

def load_game_state():
    """Load the saved game into the Python state structure."""
    state = GameState(**read_json(GAME_STATE_PATH))

    # Older saves have no colors yet; they are given once, in roster order.
    if not state.player_colors:
        palette = load_settings()["display"]["player_colors"]
        state.player_colors = default_player_colors(state.player_aliases, palette)

    return state


def save_game_state(state):
    """Write a state snapshot atomically to the save-game file."""
    temporary_path = GAME_STATE_PATH.with_suffix(".json.tmp")
    text = json.dumps(state.to_dict(), ensure_ascii=False, indent=4) + "\n"
    temporary_path.write_text(text, encoding="utf-8")
    temporary_path.replace(GAME_STATE_PATH)