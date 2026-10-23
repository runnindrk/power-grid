# -------------------------------------------------------------------------------------------------
# Imports

import random

from backend.rules.common.constants import DETERMINING_PLAYER_ORDER
from backend.rules.common.error_codes import ErrorCode
from backend.rules.common.game_state import GameState
from backend.rules.common.phase_flow import start_phase_two
from backend.rules.common.player_houses import count_houses
from backend.rules.common.player_plants import highest_plant_id

# -------------------------------------------------------------------------------------------------
# Ordering rules

def order_by_highest_plant(state: GameState):
    """Sort the players by their highest plant, highest first."""
    state.player_turn_order.sort(
        key=lambda player: highest_plant_id(state, player),
        reverse=True,
    )


def order_by_houses_and_plant(state: GameState):
    """Sort the players by number of houses, then by highest plant, most first."""
    house_counts = {}

    for player in state.player_turn_order:
        house_counts[player] = count_houses(state, player)

    # sort() keeps the old order for players that are completely tied.
    state.player_turn_order.sort(
        key=lambda player: (house_counts[player], highest_plant_id(state, player)),
        reverse=True,
    )

# -------------------------------------------------------------------------------------------------
# Phase one

def determine_initial_order(state: GameState, rng=None):
    """Set the turn order for the new cycle and start phase two."""
    if state.current_action != DETERMINING_PLAYER_ORDER or not state.player_turn_order:
        return ErrorCode.E_NOT_OKAY

    # The first cycle is random; every later cycle follows the rules.
    if state.cycles == 0:
        randomizer = rng if rng is not None else random
        randomizer.shuffle(state.player_turn_order)
    else:
        order_by_houses_and_plant(state)

    start_phase_two(state)

    return ErrorCode.E_OK
