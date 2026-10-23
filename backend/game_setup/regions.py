import random

from backend.data.files import load_number_of_areas


def create_initial_regions(map_data, number_of_players, rng=None):
    """Choose a random connected set of map regions for a new game."""
    rng = rng or random
    cities = map_data["cities_positions"]
    region_by_city = {city[0]: city[1].casefold() for city in cities}
    regions = set(region_by_city.values())
    adjacency = {region: set() for region in regions}
    matrix = [
        [value for value in row if not isinstance(value, str)]
        for row in map_data["connection_matrix"]
    ]

    for first in range(len(matrix)):
        for second in range(first + 1, len(matrix)):
            cost = matrix[first][second]

            if cost is None:
                cost = matrix[second][first]

            if cost is None:
                continue

            first_region = region_by_city[cities[first][0]]
            second_region = region_by_city[cities[second][0]]

            if first_region != second_region:
                adjacency[first_region].add(second_region)
                adjacency[second_region].add(first_region)

    area_count = load_number_of_areas()[f"{number_of_players}_players"]

    if area_count < 1 or area_count > len(regions):
        raise ValueError(f"Cannot choose {area_count} areas from a map with {len(regions)} regions.")

    chosen = [rng.choice(sorted(regions))]

    while len(chosen) < area_count:
        frontier = set()

        for region in chosen:
            frontier.update(adjacency[region])

        frontier.difference_update(chosen)

        if not frontier:
            raise ValueError(f"The map has no connected set of {area_count} regions.")

        chosen.append(rng.choice(sorted(frontier)))

    return chosen


def prepare_initial_regions(state, map_data, rng=None):
    """Choose and store the connected regions for a new game."""
    state.regions_chosen = create_initial_regions(map_data, state.number_of_players, rng)