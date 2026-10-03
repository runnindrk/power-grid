from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GAME_STATE_PATH = PROJECT_ROOT / "game_info" / "game_state" / "power_grid_game_state.json"
PLANT_DECK_PATH = PROJECT_ROOT / "game_info" / "static_info" / "power_grid_deck_set_0.json"
