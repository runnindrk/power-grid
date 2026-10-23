# -------------------------------------------------------------------------------------------------
# Houses on the map

def count_houses(state, player):
    """Return how many houses the player has on the map."""
    count = 0

    for spots in state.map_houses.values():
        for owner in spots.values():
            if owner == player:
                count += 1

    return count
