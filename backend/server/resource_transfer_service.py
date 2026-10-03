import json
from pathlib import Path
from typing import Any

from backend.rules.resource_transfer import transfer_plant_resource
from backend.rules.rules import ErrorCode, GameState
from backend.server.game_state_store import GAME_STATE_LOCK, load_game_state, save_game_state
from backend.server.paths import GAME_STATE_PATH, PLANT_DECK_PATH


def _load_plant_definitions(deck_path: Path) -> dict[int, dict[str, Any]]:
    deck = json.loads(deck_path.read_text(encoding="utf-8"))["deck"]
    return {plant["cost"]: plant for plant in deck}


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
        result = transfer_plant_resource(
            state,
            player,
            source_plant_id,
            source_slot,
            target_plant_id,
            target_slot,
            _load_plant_definitions(deck_path),
        )
        if result == ErrorCode.E_OK:
            save_game_state(state, state_path)
        return state, result
