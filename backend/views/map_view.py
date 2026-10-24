# -------------------------------------------------------------------------------------------------
# Imports

import math

from backend.rules.phase_four_building_houses.building_houses import connection_routes_from_network

# -------------------------------------------------------------------------------------------------
# Colors

def lerp(start, end, t):
    """Return the number between start and end at position t (0 is start, 1 is end), rounded."""
    return round(start + (end - start) * t)


def cost_color(cost, minimum, maximum, cost_colors):
    """Return a color for a connection cost: low costs use the low color, high costs the high color."""
    low = cost_colors["low"]
    mid = cost_colors["mid"]
    high = cost_colors["high"]

    if maximum == minimum:
        return f"rgb({mid[0]},{mid[1]},{mid[2]})"

    t = (cost - minimum) / (maximum - minimum)

    if t < 0.5:
        start = low
        end = mid
        local_t = t * 2
    else:
        start = mid
        end = high
        local_t = (t - 0.5) * 2

    red = lerp(start[0], end[0], local_t)
    green = lerp(start[1], end[1], local_t)
    blue = lerp(start[2], end[2], local_t)

    return f"rgb({red},{green},{blue})"

# -------------------------------------------------------------------------------------------------
# SVG shapes

def point_at_angle(cx, cy, radius, angle):
    """Return the (x, y) point at a given radius and angle in degrees from a center."""
    radians = math.radians(angle)

    return cx + math.cos(radians) * radius, cy + math.sin(radians) * radius


def wedge_path(cx, cy, radius, start_angle, end_angle):
    """Return an SVG path for a pie slice around a center point."""
    start_x, start_y = point_at_angle(cx, cy, radius, start_angle)
    end_x, end_y = point_at_angle(cx, cy, radius, end_angle)

    return f"M {cx} {cy} L {start_x} {start_y} A {radius} {radius} 0 0 1 {end_x} {end_y} Z"


# -------------------------------------------------------------------------------------------------
# Cities and connections

def scaled_cities(map_data, scale):
    """Return the cities with their positions multiplied by the map scale."""
    cities = []

    for name, region, x, y in map_data["cities_positions"]:
        cities.append({"name": name, "region": region, "x": x * scale, "y": y * scale})

    return cities


def connections_from_matrix(matrix):
    """Return (first city index, second city index, cost) for every pair of connected cities."""
    # City names are mixed with the numbers in the JSON file to make it easier to read.
    rows = []

    for row in matrix:
        numbers = []

        for value in row:
            if not isinstance(value, str):
                numbers.append(value)

        rows.append(numbers)

    connections = []

    for first in range(len(rows)):
        for second in range(first + 1, len(rows)):
            cost = rows[first][second]

            if cost is None:
                cost = rows[second][first]

            if cost is not None:
                connections.append((first, second, cost))

    return connections


def inactive_connection_indexes(cities, connections, active_regions):
    """Return indexes for connections that touch an inactive region."""
    inactive = set()

    for index, (first, second, _) in enumerate(connections):
        if (
            cities[first]["region"].casefold() not in active_regions
            or cities[second]["region"].casefold() not in active_regions
        ):
            inactive.add(index)

    return inactive


def connection_views(cities, connections, cost_colors, inactive_connections):
    """Return the lines between cities, and the cost labels drawn on the lines that have a cost."""
    costs = []

    for _, _, cost in connections:
        if cost != 0:
            costs.append(cost)

    minimum = min(costs)
    maximum = max(costs)
    lines = []
    cost_labels = []

    for index in range(len(connections)):
        first, second, cost = connections[index]
        start = cities[first]
        end = cities[second]
        inactive = index in inactive_connections
        classes = ["connection-line"]

        if inactive:
            classes.append("inactive")

        lines.append({
            "id": f"connection-{index}", "classes": classes,
            "x1": start["x"], "y1": start["y"], "x2": end["x"], "y2": end["y"],
        })

        if cost == 0:
            continue

        text = str(cost)

        cost_labels.append({
            "id": f"cost-{index}",
            "x": (start["x"] + end["x"]) / 2,
            "y": (start["y"] + end["y"]) / 2,
            "text": text,
            "radius": max(6.5, len(text) * 2.5 + 4),
            "color": cost_color(cost, minimum, maximum, cost_colors),
            "inactive": inactive,
        })

    return lines, cost_labels

# -------------------------------------------------------------------------------------------------
# House spots

def spot_view(config, city, spot_index, spot_count, spot, owner, players, selected, active, available,
              connection_cost, network_path_ids, network_color):
    """Describe one house spot of a city: its shape, its owner color and whether it is selected."""
    display = config["display"]
    price = config["rules"]["house_spot_costs"][spot]
    arc = 360 / spot_count
    start_angle = -90 + spot_index * arc

    classes = ["house-spot"]
    owner_name = "empty"
    face_fill = display["empty_spot_color"]

    if owner:
        classes.append("occupied")
        owner_name = players[owner]["label"]
        face_fill = players[owner]["color"]

    is_selected = (city["name"], spot) in selected
    total_price = price + connection_cost if connection_cost is not None else None
    price_label = f"price ${price}"

    if connection_cost is not None:
        price_label += f" (${price} spot + ${connection_cost} connection)"
    else:
        price_label += " (connection unavailable)"

    if is_selected:
        classes.append("selected")

    if not active:
        classes.append("inactive")

    if not available and not owner:
        classes.append("locked")

    return {
        "spot": spot,
        "city": city["name"],
        "classes": classes,
        "owner": owner,
        "price": price,
        "aria_label": f"{city['name']}, {spot.replace('_', ' ')}: {owner_name}, {price_label}",
        "aria_disabled": not available,
        "aria_pressed": is_selected,
        "face_path": wedge_path(city["x"], city["y"], display["map"]["spot_radius"], start_angle, start_angle + arc),
        "face_fill": face_fill,
        "connection_cost": connection_cost,
        "total_price": total_price,
        "network_path_ids": network_path_ids,
        "network_color": network_color,
    }

# -------------------------------------------------------------------------------------------------
# City view

def city_view(config, index, city, houses, connections, players, selected, active_regions,
              inactive_connections, current_player, step, connection_cost, network_path_ids,
              network_color):
    """Describe a city, its house spots, and the lines to highlight when hovered."""
    display = config["display"]

    spot_names = list(houses.keys())
    active = city["region"].casefold() in active_regions
    player_has_house = any(owner == current_player for owner in houses.values())
    pending_city = any(selected_city == city["name"] for selected_city, _ in selected)
    spots = []

    for spot_index in range(len(spot_names)):
        spot = spot_names[spot_index]
        is_selected = (city["name"], spot) in selected
        unlocked = int(spot.rsplit("_", 1)[-1]) <= step
        available = (
            active
            and houses[spot] is None
            and unlocked
            and not player_has_house
            and (not pending_city or is_selected)
        )
        spots.append(spot_view(
            config,
            city,
            spot_index,
            len(spot_names),
            spot,
            houses[spot],
            players,
            selected,
            active,
            available,
            connection_cost,
            network_path_ids,
            network_color,
        ))

    highlight_ids = []

    for number in range(len(connections)):
        first, second, cost = connections[number]

        if (first == index or second == index) and number not in inactive_connections:
            highlight_ids.append(f"connection-{number}")

            if cost != 0:
                highlight_ids.append(f"cost-{number}")

    label_color = display["default_label_color"]

    if city["region"] in display["region_colors"]:
        label_color = display["region_colors"][city["region"]]

    classes = ["city-node"]

    if not active:
        classes.append("inactive")

    return {
        "index": index,
        "name": city["name"],
        "region": city["region"],
        "active": active,
        "classes": classes,
        "aria_disabled": not active,
        "x": city["x"],
        "y": city["y"],
        "label_y": city["y"] + display["map"]["city_label_offset"],
        "label_color": label_color,
        "spots": spots,
        "highlight_ids": highlight_ids,
    }

# -------------------------------------------------------------------------------------------------
# Whole map

def build_map_view(config, map_data, map_houses, players, selected, active_regions, current_player, step,
                   pending_houses, player_network_routes):
    """Describe the whole map: size, cities with their house spots, lines and cost labels."""
    map_settings = config["display"]["map"]
    scale = map_settings["scale"]
    width = map_data["map_size"][0][0] * scale
    height = map_data["map_size"][0][1] * scale

    cities = scaled_cities(map_data, scale)
    connections = connections_from_matrix(map_data["connection_matrix"])
    inactive_connections = inactive_connection_indexes(cities, connections, active_regions)
    lines, cost_labels = connection_views(
        cities, connections, config["display"]["cost_colors"], inactive_connections,
    )
    line_indexes = {
        frozenset((cities[first]["name"], cities[second]["name"])): index
        for index, (first, second, _) in enumerate(connections)
    }

    city_views = []
    owned_cities = {
        city for city, houses in map_houses.items()
        if current_player in houses.values()
    }
    pending_cities = [house["city"] for house in pending_houses]
    pending_indexes = {city: index for index, city in enumerate(pending_cities)}
    route_cache = {}
    display_routes = {
        player: [list(path) for path in player_network_routes.get(player, [])]
        for player in players
    }

    for player in players:
        covered_cities = {
            path[-1]
            for path in display_routes[player]
            if path
        }
        sources = set(covered_cities)

        for city in cities:
            city_name = city["name"]

            if player not in map_houses[city_name].values() or city_name in covered_cities:
                continue

            routes = connection_routes_from_network(map_data, active_regions, sources)
            route = routes.get(city_name)

            if route:
                display_routes[player].append(route["path"])

            sources.add(city_name)

    for index in range(len(cities)):
        houses = map_houses[cities[index]["name"]]
        city_name = cities[index]["name"]
        pending_index = pending_indexes.get(city_name)
        connected_cities = set(pending_cities if pending_index is None else pending_cities[:pending_index])
        network = frozenset(owned_cities | connected_cities)

        if network not in route_cache:
            route_cache[network] = connection_routes_from_network(map_data, active_regions, network)

        route = route_cache[network].get(city_name)
        connection_cost = route["cost"] if route else None
        network_path_ids = []

        if pending_index is not None and route:
            display_routes.setdefault(current_player, []).append(route["path"])

        if route:
            for first, second in zip(route["path"], route["path"][1:]):
                line_index = line_indexes[frozenset((first, second))]
                network_path_ids.append(f"connection-{line_index}")

        city_views.append(city_view(
            config,
            index,
            cities[index],
            houses,
            connections,
            players,
            selected,
            active_regions,
            inactive_connections,
            current_player,
            step,
            connection_cost,
            network_path_ids,
            players.get(current_player, {}).get("color"),
        ))

    edge_owners = [set() for _ in connections]

    for player, paths in display_routes.items():
        for path in paths:
            for first, second in zip(path, path[1:]):
                edge_index = line_indexes.get(frozenset((first, second)))

                if edge_index is not None:
                    edge_owners[edge_index].add(player)

    for index, line in enumerate(lines):
        line["network_colors"] = [
            {"player": player, "color": players[player]["color"]}
            for player in players
            if player in edge_owners[index]
        ]

    text = config["text"]

    return {
        "width": width,
        "height": height,
        "boundary": {"x": 1, "y": 1, "width": width - 2, "height": height - 2},
        "outline_url": map_settings["outline_url"],
        "selection_color": players.get(current_player, {}).get("color"),
        "stats": text["stats_line"].format(title=text["map_title"], cities=len(cities), connections=len(connections)),
        "lines": lines,
        "cost_labels": cost_labels,
        "cities": city_views,
    }
