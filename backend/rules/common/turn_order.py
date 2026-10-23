# -------------------------------------------------------------------------------------------------
# Imports

from backend.rules.common.error_codes import ErrorCode

# -------------------------------------------------------------------------------------------------
# Turn order

def next_player(state, player, candidates):
    """Return the first candidate after the player in turn order, or None if there is none."""
    turn_order = state.player_turn_order
    start = turn_order.index(player)

    # Walk the whole circle, ending with the player themselves.
    for step in range(1, len(turn_order) + 1):
        candidate = turn_order[(start + step) % len(turn_order)]

        if candidate in candidates:
            return candidate

    return None


def previous_player(state, player, candidates):
    """Return the first candidate before the player in turn order, wrapping around."""
    turn_order = state.player_turn_order
    start = turn_order.index(player)

    for step in range(1, len(turn_order) + 1):
        candidate = turn_order[(start - step) % len(turn_order)]

        if candidate in candidates:
            return candidate

    return None


def advance_turn(state, player):
    """Give the turn to the next player in turn order; only the current player may end their turn."""
    if player != state.current_player or player not in state.player_turn_order:
        return ErrorCode.E_NOT_OKAY

    state.current_player = next_player(state, player, state.player_turn_order)

    return ErrorCode.E_OK


def advance_turn_reverse(state, player):
    """Give the turn to the previous player without changing stored player order."""
    if player != state.current_player or player not in state.player_turn_order:
        return ErrorCode.E_NOT_OKAY

    state.current_player = previous_player(state, player, state.player_turn_order)

    return ErrorCode.E_OK
