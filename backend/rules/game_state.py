# -------------------------------------------------------------------------------------------------
# Imports

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from threading import RLock

from backend.data.files import GAME_STATE_PATH, read_json

# -------------------------------------------------------------------------------------------------
# Game state

@dataclass
class GameState:
    number_of_players: int
    regions_chosen: list[str]
    rounds_played: int
    step: int
    phase: int
    power_plant_market: list[int]
    back_of_the_next_card: str
    resource_market: dict[str, int]
    player_turn_order: list[str]
    current_player: str
    current_action: str
    player_aliases: dict[str, str]
    player_money: dict[str, int]
    player_power_plants: dict[str, list[dict]]
    map_houses: dict[str, dict[str, str | None]]
    pending_houses: list[dict[str, str]]

    def to_dict(self):
        return asdict(self)


def load_game_state():
    """Load the saved game into the Python state structure."""
    return GameState(**read_json(GAME_STATE_PATH))


GAME_STATE_LOCK = RLock()
GAME_STATE = load_game_state()


def get_game_state():
    return GAME_STATE


def save_game_state():
    with GAME_STATE_LOCK:
        temporary_path = GAME_STATE_PATH.with_suffix(".json.tmp")
        text = json.dumps(GAME_STATE.to_dict(), ensure_ascii=False, indent=4) + "\n"
        temporary_path.write_text(text, encoding="utf-8")
        temporary_path.replace(GAME_STATE_PATH)