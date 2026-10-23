# -------------------------------------------------------------------------------------------------
# Imports

from backend.rules.common.constants import (
    BUILDING_HOUSES,
    BUREAUCRACY,
    BUYING_RESOURCES,
    PHASE_ONE_TURN_ORDER,
    PHASE_TWO_AUCTION,
    POWER_PLANT_AUCTION,
)
from backend.rules.common.phase_state import clear_phase_finished

# -------------------------------------------------------------------------------------------------
# Phase starts
# Each function moves the game into a phase; the first player in turn order acts first.

def start_phase_two(state):
    """Start the power plant auction."""
    clear_phase_finished(state, PHASE_ONE_TURN_ORDER)

    state.phase = 2
    state.current_action = POWER_PLANT_AUCTION
    state.current_player = state.player_turn_order[0]


def start_phase_three(state):
    """Start resource buying; the auction state is cleared first."""
    clear_phase_finished(state, PHASE_TWO_AUCTION)

    state.phase = 3
    state.current_action = BUYING_RESOURCES
    state.current_player = state.player_turn_order[-1]
    state.pending_resource_purchase.clear()
    state.pending_resource_player = None
    state.pending_resource_price = 0


def start_phase_four(state):
    """Start building houses."""
    state.phase = 4
    state.current_action = BUILDING_HOUSES
    state.current_player = state.player_turn_order[-1]


def start_phase_five(state):
    """Start bureaucracy."""
    state.phase = 5
    state.current_action = BUREAUCRACY
    state.current_player = state.player_turn_order[0]
