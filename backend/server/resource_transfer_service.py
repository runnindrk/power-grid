import json
from pathlib import Path
from typing import Any

from backend.rules.resource_transfer import transfer_plant_resource
from backend.rules.rules import ErrorCode, GameState
from backend.server.game_state_store import (
    GAME_STATE_LOCK,
    GAME_STATE_PATH,
    load_game_state,
    save_game_state,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PLANT_DECK_PATH = PROJECT_ROOT / "game_info" / "static_info" / "power_grid_deck_set_0.json"


def transfer_resource(
    player: str,
    source_plant_id: int,
    source_slot: int,
    target_plant_id: int,
    target_slot: int,
    state_path: Path = GAME_STATE_PATH,
    deck_path: Path = PLANT_DECK_PATH,
) -> tuple[GameState, ErrorCode]:
    with GAME_STATE_LOCK:
        state = load_game_state(state_path)
        with deck_path.open(encoding="utf-8") as deck_file:
            deck = json.load(deck_file)["deck"]
        plant_definitions = {plant["cost"]: plant for plant in deck}
        result = transfer_plant_resource(
            state,
            player,
            source_plant_id,
            source_slot,
            target_plant_id,
            target_slot,
            plant_definitions,
        )
        if result == ErrorCode.E_OK:
            save_game_state(state, state_path)
        return state, result
