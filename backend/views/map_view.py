# -------------------------------------------------------------------------------------------------
# Imports

import math

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


def house_path(cx, cy):
    """Return an SVG path for a small house icon centered on a point."""
    return (
        f"M {cx - 4} {cy} L {cx} {cy - 3.5} L {cx + 4} {cy} V {cy + 4} "
        f"H {cx + 1.5} V {cy + 1} H {cx - 1.5} V {cy + 4} H {cx - 4} Z"
    )

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


def connection_views(cities, connections, cost_colors):
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

        lines.append({
            "id": f"connection-{index}",
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
        })

    return lines, cost_labels

# -------------------------------------------------------------------------------------------------
# House spots

def spot_view(config, city, spot_index, spot_count, spot, owner, players, selected):
    """Describe one house spot of a city: its shape, its owner color and whether it is selected."""
    display = config["display"]
    arc = 360 / spot_count
    start_angle = -90 + spot_index * arc
    mark_x, mark_y = point_at_angle(city["x"], city["y"], display["map"]["mark_radius"], start_angle + arc / 2)

    classes = ["house-spot"]
    owner_name = "empty"
    face_fill = display["empty_spot_color"]
    mark_display = "none"

    if owner:
        classes.append("occupied")
        owner_name = players[owner]["label"]
        face_fill = players[owner]["color"]
        mark_display = "inline"

    is_selected = (city["name"], spot) in selected

    if is_selected:
        classes.append("selected")

    return {
        "spot": spot,
        "city": city["name"],
        "classes": classes,
        "owner": owner,
        "aria_label": f"{city['name']}, {spot.replace('_', ' ')}: {owner_name}",
        "aria_disabled": bool(owner),
        "aria_pressed": is_selected,
        "face_path": wedge_path(city["x"], city["y"], display["map"]["spot_radius"], start_angle, start_angle + arc),
        "face_fill": face_fill,
        "mark_path": house_path(mark_x, mark_y),
        "mark_display": mark_display,
    }

# -------------------------------------------------------------------------------------------------
# City view

def city_view(config, index, city, houses, connections, players, selected):
    """Describe a city: its house spots, its label, its tooltip and the lines to highlight when hovered."""
    display = config["display"]
    text = config["text"]

    spot_names = list(houses.keys())
    spots = []
    owned = 0

    for spot_index in range(len(spot_names)):
        spot = spot_names[spot_index]
        spots.append(spot_view(config, city, spot_index, len(spot_names), spot, houses[spot], players, selected))

        if houses[spot]:
            owned += 1

    highlight_ids = []
    connection_count = 0

    for number in range(len(connections)):
        first, second, cost = connections[number]

        if first == index or second == index:
            connection_count += 1
            highlight_ids.append(f"connection-{number}")

            if cost != 0:
                highlight_ids.append(f"cost-{number}")

    label_color = display["default_label_color"]

    if city["region"] in display["region_colors"]:
        label_color = display["region_colors"][city["region"]]

    return {
        "index": index,
        "name": city["name"],
        "x": city["x"],
        "y": city["y"],
        "label_y": city["y"] + display["map"]["city_label_offset"],
        "label_color": label_color,
        "spots": spots,
        "highlight_ids": highlight_ids,
        "tooltip": {
            "title": city["name"],
            "lines": [
                text["region_line"].format(region=city["region"]),
                text["connections_line"].format(count=connection_count),
                text["houses_line"].format(owned=owned, total=len(spot_names)),
            ],
        },
    }

# -------------------------------------------------------------------------------------------------
# Whole map

def build_map_view(config, map_data, map_houses, players, selected):
    """Describe the whole map: size, cities with their house spots, lines and cost labels."""
    map_settings = config["display"]["map"]
    scale = map_settings["scale"]
    width = map_data["map_size"][0][0] * scale
    height = map_data["map_size"][0][1] * scale

    cities = scaled_cities(map_data, scale)
    connections = connections_from_matrix(map_data["connection_matrix"])
    lines, cost_labels = connection_views(cities, connections, config["display"]["cost_colors"])

    city_views = []

    for index in range(len(cities)):
        houses = map_houses[cities[index]["name"]]
        city_views.append(city_view(config, index, cities[index], houses, connections, players, selected))

    text = config["text"]

    return {
        "width": width,
        "height": height,
        "boundary": {"x": 1, "y": 1, "width": width - 2, "height": height - 2},
        "outline_url": map_settings["outline_url"],
        "stats": text["stats_line"].format(title=text["map_title"], cities=len(cities), connections=len(connections)),
        "lines": lines,
        "cost_labels": cost_labels,
        "cities": city_views,
    }
