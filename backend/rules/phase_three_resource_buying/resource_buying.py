# -------------------------------------------------------------------------------------------------
# Imports

from backend.rules.common.error_codes import ErrorCode
from backend.rules.common.game_state import GameState

# -------------------------------------------------------------------------------------------------
# Phase three: buying resources

def quote_resources(state: GameState, player, resources):
    """Placeholder: return the price of resources for a player."""
    return 0


def buy_resources(state: GameState, player, resources):
    """Placeholder: buy resources for a player."""
    return ErrorCode.E_OK
