# -------------------------------------------------------------------------------------------------
# Imports

from backend.data.files import load_plant_deck, load_resources
from backend.rules.game_state import (
    GAME_STATE_LOCK,
    get_game_state,
)
from backend.rules.resource_transfer import find_player_plant, transfer_plant_resource
from backend.rules.rules import ErrorCode

# -------------------------------------------------------------------------------------------------
# House spots

def toggle_house_spot(city, spot):
    """Add or remove a free city spot from the pending houses in the game state."""
    with GAME_STATE_LOCK:
        state = get_game_state()
        spots = state.map_houses.get(city)

        if spots is None or spot not in spots or spots[spot] is not None:
            return ErrorCode.E_NOT_OKAY

        selection = {"city": city, "spot": spot}
        if selection in state.pending_houses:
            state.pending_houses.remove(selection)
        else:
            state.pending_houses.append(selection)

        return ErrorCode.E_OK

# -------------------------------------------------------------------------------------------------
# Ready to power

def toggle_ready_to_power(player, plant_id):
    """Flip the ready-to-power flag on one of the player's plants in the game state."""
    with GAME_STATE_LOCK:
        state = get_game_state()
        plant = find_player_plant(state, player, plant_id)

        if plant is None:
            return ErrorCode.E_NOT_OKAY

        plant.ready_to_power = not plant.ready_to_power

        return ErrorCode.E_OK

# -------------------------------------------------------------------------------------------------
# Resource transfer

def transfer_resource(player, source_plant_id, source_slot, target_plant_id, target_slot):
    """Move one fuel unit between two of the player's plants and save the game state if the move is valid."""
    with GAME_STATE_LOCK:
        state = get_game_state()

        result = transfer_plant_resource(
            state, player, source_plant_id, source_slot, target_plant_id, target_slot,
            load_plant_deck(), load_resources()["resources"],
        )

        return result
