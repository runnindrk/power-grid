# -------------------------------------------------------------------------------------------------
# Imports

import json

from backend.data.files import GAME_STATE_PATH, read_json
from backend.rules.common.game_state import GameState

# -------------------------------------------------------------------------------------------------
# Game state persistence

def load_game_state():
    """Load the saved game into the Python state structure."""
    return GameState(**read_json(GAME_STATE_PATH))


def save_game_state(state):
    """Write a state snapshot atomically to the save-game file."""
    temporary_path = GAME_STATE_PATH.with_suffix(".json.tmp")
    text = json.dumps(state.to_dict(), ensure_ascii=False, indent=4) + "\n"
    temporary_path.write_text(text, encoding="utf-8")
    temporary_path.replace(GAME_STATE_PATH)