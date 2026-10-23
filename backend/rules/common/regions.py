def regions_in_play(state, area_counts):
    """Return the configured number of chosen regions as normalized region IDs."""
    count = area_counts[f"{state.number_of_players}_players"]

    return {region.casefold() for region in state.regions_chosen[:count]}