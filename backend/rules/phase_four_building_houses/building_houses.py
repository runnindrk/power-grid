import heapq

from backend.rules.common.error_codes import ErrorCode
from backend.rules.common.game_state import GameState


def _city_graph(map_data, active_regions):
    cities = map_data["cities_positions"]
    names = [city[0] for city in cities]
    regions = {city[0]: city[1].casefold() for city in cities}
    matrix = [
        [value for value in row if not isinstance(value, str)]
        for row in map_data["connection_matrix"]
    ]
    graph = {name: {} for name in names if regions[name] in active_regions}

    for first in range(len(matrix)):
        first_city = names[first]

        if first_city not in graph:
            continue

        for second in range(first + 1, len(matrix)):
            second_city = names[second]

            if second_city not in graph:
                continue

            cost = matrix[first][second]

            if cost is None:
                cost = matrix[second][first]

            if cost is not None:
                graph[first_city][second_city] = cost
                graph[second_city][first_city] = cost

    return graph


def _connection_cost(sources, target, graph):
    if not sources:
        return 0

    costs = _connection_costs(sources, graph)
    return costs.get(target)


def _connection_tree(sources, graph):
    if not sources:
        return {city: 0 for city in graph}, {}

    distances = [(0, city) for city in sources if city in graph]
    heapq.heapify(distances)
    best = {city: 0 for _, city in distances}
    previous = {}

    while distances:
        distance, city = heapq.heappop(distances)

        if distance != best[city]:
            continue

        for neighbor, cost in graph[city].items():
            next_distance = distance + cost

            if next_distance < best.get(neighbor, float("inf")):
                best[neighbor] = next_distance
                previous[neighbor] = city
                heapq.heappush(distances, (next_distance, neighbor))

    return best, previous


def _connection_costs(sources, graph):
    costs, _ = _connection_tree(sources, graph)
    return costs


def connection_costs_from_network(map_data, active_regions, sources):
    """Return each active city's cheapest connection cost from the supplied network."""
    graph = _city_graph(map_data, active_regions)
    return _connection_costs(sources, graph)


def connection_routes_from_network(map_data, active_regions, sources):
    """Return each active city's cheapest connection cost and route from the network."""
    graph = _city_graph(map_data, active_regions)
    costs, previous = _connection_tree(sources, graph)
    routes = {}

    for city, cost in costs.items():
        path = [city]

        while path[-1] in previous:
            path.append(previous[path[-1]])

        path.reverse()
        routes[city] = {"cost": cost, "path": path}

    return routes


def _placement_price(state: GameState, player, placements, map_data, active_regions, spot_costs):
    if not isinstance(placements, list):
        return None

    graph = _city_graph(map_data, active_regions)
    sources = {
        city
        for city, spots in state.map_houses.items()
        if city in graph and player in spots.values()
    }
    selected_cities = set()
    total = 0

    for placement in placements:
        if not isinstance(placement, dict):
            return None

        city = placement.get("city")
        spot = placement.get("spot")

        if city not in graph or city not in state.map_houses:
            return None
        if spot not in state.map_houses[city] or spot not in spot_costs:
            return None
        if state.map_houses[city][spot] is not None:
            return None
        if int(spot.rsplit("_", 1)[-1]) > state.step:
            return None
        if city in selected_cities or city in sources:
            return None

        connection = _connection_cost(sources, city, graph)

        if connection is None:
            return None

        total += spot_costs[spot] + connection
        selected_cities.add(city)
        sources.add(city)

    return total


def quote_houses(state: GameState, player, placements, map_data, active_regions, spot_costs):
    """Return spot prices plus connection costs, or None for invalid placements."""
    return _placement_price(state, player, placements, map_data, active_regions, spot_costs)


def buy_houses(state: GameState, player, placements, map_data, active_regions, spot_costs):
    """Charge and place all selected houses if the complete selection is affordable."""
    price = _placement_price(state, player, placements, map_data, active_regions, spot_costs)

    if price is None or price > state.player_money.get(player, -1):
        return ErrorCode.E_NOT_OKAY

    sources = {
        city
        for city, spots in state.map_houses.items()
        if player in spots.values()
    }
    routes = []

    for placement in placements:
        city = placement["city"]
        route = connection_routes_from_network(map_data, active_regions, sources).get(city)
        routes.append(route["path"] if route else [city])
        sources.add(city)

    state.player_money[player] -= price

    for placement in placements:
        state.map_houses[placement["city"]][placement["spot"]] = player

    state.player_network_routes.setdefault(player, []).extend(routes)
    state.pending_houses.clear()

    return ErrorCode.E_OK