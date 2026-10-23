PHASE_BY_ACTION = {
    "determining_player_order": "phase_one_turn_order",
    "power_plant_auction": "phase_two_auction",
    "power_plant_bidding": "phase_two_auction",
    "discard_power_plant": "phase_two_auction",
    "buying_resources": "phase_three_resource_buying",
    "building_houses": "phase_four_building_houses",
    "bureaucracy": "phase_five_bureaucracy",
}


def phase_key(action):
    """Group sub-actions under their parent phase for shared phase-level state."""
    return PHASE_BY_ACTION.get(action, action)


def mark_phase_finished(state, phase, player):
    """Record one player's completion of a phase without adding duplicates."""
    finished_players = state.phase_finished_players.setdefault(phase_key(phase), [])
    if player not in finished_players:
        finished_players.append(player)


def clear_phase_finished(state, phase):
    """Remove completion marks when a phase ends."""
    state.phase_finished_players.pop(phase_key(phase), None)


def all_players_finished(state, phase):
    """Return whether every player has completed the named phase."""
    finished_players = set(state.phase_finished_players.get(phase_key(phase), []))
    return all(player in finished_players for player in state.player_turn_order)