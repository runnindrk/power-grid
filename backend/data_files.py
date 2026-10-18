# -------------------------------------------------------------------------------------------------
# Imports

import json
from pathlib import Path
from threading import Lock

# -------------------------------------------------------------------------------------------------
# Constants

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GAME_INFO = PROJECT_ROOT / "game_info"

GAME_STATE_PATH = GAME_INFO / "game_state" / "power_grid_game_state.json"
SETTINGS_PATH = GAME_INFO / "static_info" / "power_grid_settings.json"
RESOURCES_PATH = GAME_INFO / "static_info" / "power_grid_resource_prices.json"
PLANT_DECK_PATH = GAME_INFO / "static_info" / "power_grid_deck_set_0.json"
MONEY_PATH = GAME_INFO / "static_info" / "power_grid_money.json"
REPLENISHMENT_PATH = GAME_INFO / "static_info" / "power_grid_replenishment.json"
MAP_PATH = GAME_INFO / "maps" / "germany" / "power_grid_germany_map.json"

# Held while the game state is read, changed and saved, so two requests can't overwrite each other.
GAME_STATE_LOCK = Lock()

# -------------------------------------------------------------------------------------------------
# File reading

def read_json(path):
    """Read a JSON file and return its content."""
    text = path.read_text(encoding="utf-8")

    return json.loads(text)

# -------------------------------------------------------------------------------------------------
# Game state

def load_game_state():
    """Return the game state; this file is the only place the game state lives."""
    return read_json(GAME_STATE_PATH)


def save_game_state(state):
    """Write the game state to a temporary file, then replace the real file with it."""
    temporary_path = GAME_STATE_PATH.with_suffix(".json.tmp")
    text = json.dumps(state, ensure_ascii=False, indent=4) + "\n"

    temporary_path.write_text(text, encoding="utf-8")
    temporary_path.replace(GAME_STATE_PATH)

# -------------------------------------------------------------------------------------------------
# Static game data

def load_settings():
    """Return the rules, texts and colors (power_grid_settings.json)."""
    return read_json(SETTINGS_PATH)


def load_resources():
    """Return the price scales and the resource list (power_grid_resource_prices.json)."""
    return read_json(RESOURCES_PATH)


def load_plant_deck():
    """Return the power plants indexed by cost, which is also the plant id."""
    plants = {}

    for plant in read_json(PLANT_DECK_PATH)["deck"]:
        plants[plant["cost"]] = plant

    return plants


def load_money():
    """Return the income table by number of houses."""
    return read_json(MONEY_PATH)


def load_replenishment():
    """Return the resource replenishment by player count and step."""
    return read_json(REPLENISHMENT_PATH)


def load_map():
    """Return the map: city positions, map size and connection costs."""
    return read_json(MAP_PATH)
