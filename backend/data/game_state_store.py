# -------------------------------------------------------------------------------------------------
# Imports

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.data.files import GAME_SAVE_DIR, load_plant_deck, load_settings, read_json
from backend.rules.common.game_state import GameState, default_player_colors

# -------------------------------------------------------------------------------------------------
# Game state persistence

SAVE_FILENAME = re.compile(r"^power_grid_game_save_(\d{8}T\d{6}(?:_\d{1,6})?Z)\.json$")


def _save_timestamp(save_id):
    match = SAVE_FILENAME.fullmatch(save_id)

    if match is None:
        raise ValueError("Invalid game save identifier.")

    timestamp = match.group(1)
    timestamp_format = "%Y%m%dT%H%M%S_%fZ" if "_" in timestamp else "%Y%m%dT%H%M%SZ"

    return datetime.strptime(timestamp, timestamp_format).replace(tzinfo=timezone.utc)


def list_saved_games():
    """Return valid game saves, newest first, with their timestamp and player count."""
    saves = []

    if not GAME_SAVE_DIR.is_dir():
        return saves

    for path in GAME_SAVE_DIR.iterdir():
        if not path.is_file() or SAVE_FILENAME.fullmatch(path.name) is None:
            continue

        try:
            saved_state = read_json(path)
            saved_at = _save_timestamp(path.name)
        except (OSError, ValueError, json.JSONDecodeError):
            continue

        saves.append({
            "id": path.name,
            "saved_at": saved_at.isoformat(),
            "number_of_players": saved_state.get("number_of_players"),
        })

    saves.sort(key=lambda save: _save_timestamp(save["id"]), reverse=True)

    return saves


def _save_path(save_id=None):
    saves = list_saved_games()

    if save_id is None:
        if not saves:
            raise FileNotFoundError("No saved games are available.")

        save_id = saves[0]["id"]

    if not isinstance(save_id, str) or SAVE_FILENAME.fullmatch(save_id) is None:
        raise ValueError("Invalid game save identifier.")

    path = GAME_SAVE_DIR / save_id

    if not path.is_file():
        raise FileNotFoundError("The requested game save does not exist.")

    return path


def load_game_state(save_id=None):
    """Load a selected timestamped game save into the Python state structure."""
    state = GameState(**read_json(_save_path(save_id)))

    for card_id, card in load_plant_deck().items():
        if "cost" not in card and isinstance(card_id, str) and card_id.startswith("Step "):
            card_step = int(card_id.split()[-1])

            if state.step < card_step and card_id not in state.power_plant_deck:
                state.power_plant_deck.append(card_id)

    # Older saves have no colors yet; they are given once, in roster order.
    if not state.player_colors:
        palette = load_settings()["display"]["player_colors"]
        state.player_colors = default_player_colors(state.player_aliases, palette)

    return state


def save_game_state(state):
    """Write a uniquely timestamped game save atomically and return its filename."""
    GAME_SAVE_DIR.mkdir(parents=True, exist_ok=True)
    saved_at = datetime.now(timezone.utc)

    while True:
        timestamp = saved_at.strftime("%Y%m%dT%H%M%S_%fZ")
        save_path = GAME_SAVE_DIR / f"power_grid_game_save_{timestamp}.json"

        if not save_path.exists():
            break

        saved_at += timedelta(microseconds=1)

    temporary_path = save_path.with_suffix(".json.tmp")
    text = json.dumps(state.to_dict(), ensure_ascii=False, indent=4) + "\n"
    temporary_path.write_text(text, encoding="utf-8")
    temporary_path.replace(save_path)

    return save_path.name