# -------------------------------------------------------------------------------------------------
# Imports

from pathlib import Path
import sys

# Must run before the backend imports so the script also works when started directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.data.files import load_settings
from backend.data.game_state_store import load_game_state, save_game_state
from backend.server.app import create_app

# -------------------------------------------------------------------------------------------------
# The real game: the save game file, with real saving

plant_slots = load_settings()["rules"]["plant_slots_per_player"]
app = create_app(
    load_state=load_game_state,
    save_state=save_game_state,
    plant_slots_per_player=plant_slots,
)

# -------------------------------------------------------------------------------------------------
# Main

if __name__ == "__main__":
    app.run(port=8000, debug=True)
