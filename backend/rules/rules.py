# -------------------------------------------------------------------------------------------------
# Imports

from enum import IntEnum

from backend.rules.game_state import GameState

# -------------------------------------------------------------------------------------------------
# Result codes

class ErrorCode(IntEnum):
    E_OK = 0
    E_NOT_OKAY = 1

# -------------------------------------------------------------------------------------------------
# Phase 2: Power plant auction (placeholders)

def place_bid(state: GameState, player, amount):
    """Placeholder: will record a bid from a player in the auction."""
    return ErrorCode.E_OK


def select_power_plant(state: GameState, plant_id):
    """Select a market plant for the current auction phase."""
    if state.current_action != "power_plant_auction" or plant_id not in state.power_plant_market:
        return ErrorCode.E_NOT_OKAY

    state.selected_power_plant = plant_id
    return ErrorCode.E_OK


def pass_bid(state: GameState, player):
    """Placeholder: will record that a player is out of the auction."""
    return ErrorCode.E_OK

# -------------------------------------------------------------------------------------------------
# Phase 3: Resource buying (placeholders)

def quote_resources(state: GameState, player, resources):
    """Placeholder: will return the price of the resources; always 0 for now."""
    return 0


def buy_resources(state: GameState, player, resources):
    """Placeholder: will buy the resources for a player."""
    return ErrorCode.E_OK

# -------------------------------------------------------------------------------------------------
# Phase 4: Building houses (placeholders)

def quote_houses(state: GameState, player, placements):
    """Placeholder: will return the price of the houses; always 0 for now."""
    return 0


def buy_houses(state: GameState, player, placements):
    """Placeholder: will buy houses in the selected city spots for a player."""
    return ErrorCode.E_OK

# -------------------------------------------------------------------------------------------------
# Phase 5: Bureaucracy (placeholders)

def bureaucracy(state):
    """Placeholder: will run the bureaucracy phase (powering plants and income)."""
    return ErrorCode.E_OK
