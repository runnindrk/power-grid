from backend.rules.common.error_codes import ErrorCode
from backend.rules.common.game_state import GameState


def advance_turn(state: GameState, player):
    """Advance to the next player if the acting player owns the current turn."""
    if player != state.current_player or player not in state.player_turn_order:
        return ErrorCode.E_NOT_OKAY

    current_index = state.player_turn_order.index(player)
    next_index = (current_index + 1) % len(state.player_turn_order)
    state.current_player = state.player_turn_order[next_index]

    return ErrorCode.E_OK