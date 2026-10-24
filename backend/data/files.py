# -------------------------------------------------------------------------------------------------
# Imports

import json
from pathlib import Path

# -------------------------------------------------------------------------------------------------
# Constants

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GAME_INFO = PROJECT_ROOT / "game_info"

GAME_SAVE_DIR = GAME_INFO / "game_save"
SETTINGS_PATH = GAME_INFO / "static_info" / "power_grid_settings.json"
RESOURCES_PATH = GAME_INFO / "static_info" / "power_grid_resource_prices.json"
PLANT_DECK_PATH = GAME_INFO / "static_info" / "power_grid_deck_set_0.json"
MONEY_PATH = GAME_INFO / "static_info" / "power_grid_money.json"
REPLENISHMENT_PATH = GAME_INFO / "static_info" / "power_grid_replenishment.json"
PLANT_REMOVAL_PATH = GAME_INFO / "static_info" / "power_grid_plant_removal.json"
NUMBER_OF_AREAS_PATH = GAME_INFO / "static_info" / "power_grid_number_of_areas.json"
MAP_PATH = GAME_INFO / "maps" / "germany" / "power_grid_germany_map.json"

# -------------------------------------------------------------------------------------------------
# File reading

def read_json(path):
    """Read a JSON file and return its content."""
    text = path.read_text(encoding="utf-8")

    return json.loads(text)

# -------------------------------------------------------------------------------------------------
# Static game data

def load_settings():
    """Return the rules, texts and colors (power_grid_settings.json)."""
    return read_json(SETTINGS_PATH)


def load_resources():
    """Return the price scales and the resource list (power_grid_resource_prices.json)."""
    return read_json(RESOURCES_PATH)


def load_plant_deck():
    """Return cards indexed by ID; ordinary plant IDs remain their costs."""
    plants = {}

    for plant in read_json(PLANT_DECK_PATH)["deck"]:
        plant_id = plant["id"] if "id" in plant else plant["cost"]
        plants[plant_id] = plant

    return plants


def load_money():
    """Return the income table by number of houses."""
    return read_json(MONEY_PATH)


def load_replenishment():
    """Return the resource replenishment by player count and step."""
    return read_json(REPLENISHMENT_PATH)


def load_plant_removal():
    """Return how many plug and non-plug plants to remove by player count."""
    return read_json(PLANT_REMOVAL_PATH)


def load_number_of_areas():
    """Return the number of playable map areas for each player count."""
    return read_json(NUMBER_OF_AREAS_PATH)


def load_map():
    """Return the map: city positions, map size and connection costs."""
    return read_json(MAP_PATH)