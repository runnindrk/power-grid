# -------------------------------------------------------------------------------------------------
# Imports

from backend.rules.common.constants import PHASE_BY_ACTION

# -------------------------------------------------------------------------------------------------
# Phase completion markers

def phase_key(action):
    """Return the phase an action belongs to; a phase name maps to itself."""
    return PHASE_BY_ACTION.get(action, action)


def mark_phase_finished(state, phase, player):
    """Record that a player finished the phase; a player is never recorded twice."""
    finished_players = state.phase_finished_players.setdefault(phase_key(phase), [])

    if player not in finished_players:
        finished_players.append(player)


def clear_phase_finished(state, phase):
    """Remove all completion marks of a phase."""
    state.phase_finished_players.pop(phase_key(phase), None)


def all_players_finished(state, phase):
    """Return True when every player has finished the phase."""
    finished_players = state.phase_finished_players.get(phase_key(phase), [])

    for player in state.player_turn_order:
        if player not in finished_players:
            return False

    return True
