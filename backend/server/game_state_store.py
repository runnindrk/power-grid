import json
from pathlib import Path
from threading import RLock
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GAME_STATE_PATH = PROJECT_ROOT / "game_info" / "game_state" / "power_grid_game_state.json"
GAME_STATE_LOCK = RLock()


def load_game_state(path: Path = GAME_STATE_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_game_state(state: dict[str, Any], path: Path = GAME_STATE_PATH) -> None:
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(path)
