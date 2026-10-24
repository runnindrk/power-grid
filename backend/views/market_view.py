# -------------------------------------------------------------------------------------------------
# Imports

from backend.rules.common.game_state import GameState
from backend.rules.phase_two_auction.auction import can_select_plant
from backend.views.plant_view import plant_card

# -------------------------------------------------------------------------------------------------
# Shared helpers

def leading_number(text):
    """Return the number at the start of a key, e.g. '03_houses' -> 3 and '2_step' -> 2."""
    return int(text.split("_")[0])

# -------------------------------------------------------------------------------------------------
# Power plant market

def power_plant_market_view(config, state: GameState, deck):
    """Describe the plants in the market: which can be selected and which is selected."""
    cards = []

    for plant_id in state.power_plant_market:
        card = plant_card(config, plant_id, deck.get(plant_id), False)
        card["selectable"] = can_select_plant(state, plant_id)
        card["selected"] = plant_id == state.selected_power_plant

        if card["selectable"]:
            card["classes"].append("selectable")

        if card["selected"]:
            card["classes"].append("selected")

        cards.append(card)

    return cards


def next_card_back_view(config, state: GameState, deck):
    """Describe the back of the top card of the draw pile, if one remains."""
    text = config["text"]
    classes = ["info-card", "next-card-back"]
    label = ""

    if state.power_plant_deck:
        next_card = state.power_plant_deck[0]
        definition = deck[next_card]
        back = definition["back_of_the_card"]

        classes.append(back)
        label = definition.get("name", next_card if isinstance(next_card, str) else text["back_of_the_card"][back])

    return {
        "heading": text["next_card_heading"],
        "classes": classes,
        "label": label,
    }

# -------------------------------------------------------------------------------------------------
# Resource market

def widest_price_scale(price_scales):
    """Return the longest price scale, which sets how many columns the resource market has."""
    widest = []

    for name in price_scales:
        if len(price_scales[name]) > len(widest):
            widest = price_scales[name]

    return widest


def rack_tiers(resource, price_scale, columns, available):
    """Describe the tiers of one resource rack; slots are filled from the cheapest price up."""
    tiers = []

    for tier_index in range(columns):
        # The rack has fewer prices than the widest rack, so this column stays empty.
        if tier_index >= len(price_scale):
            tiers.append({"empty": True, "classes": ["resource-tier", "resource-tier-empty"], "slots": []})
            continue

        slots = []

        for slot_index in range(resource["slots_per_tier"]):
            resource_index = tier_index * resource["slots_per_tier"] + slot_index

            if resource_index >= resource["capacity"]:
                break

            classes = ["resource-slot"]

            if resource_index >= resource["capacity"] - available:
                classes.append("filled")

            slots.append({"classes": classes})

        tiers.append({"empty": False, "classes": ["resource-tier"], "slots": slots})

    return tiers


def resource_market_view(config, state: GameState):
    """Describe the resource market: the price row and one rack for each resource sold there."""
    widest = widest_price_scale(config["price_scales"])
    columns = len(widest)
    racks = []

    for resource in config["resources"]:
        if not resource["market"]:
            continue

        available = state.resource_market[resource["id"]]
        label = resource["market_label"]
        price_scale = config["price_scales"][resource["price_scale"]]

        racks.append({
            "classes": ["resource-rack", "resource-" + resource["id"]],
            "icon": resource["icon"],
            "label": label,
            "title": label,
            "aria_label": f"{label}: {available} available of {resource['capacity']} spaces",
            "tiers": rack_tiers(resource, price_scale, columns, available),
        })

    return {
        "grid_template_columns": f"repeat({columns}, minmax(0, 1fr))",
        "price_row": {"prices": widest},
        "racks": racks,
    }

# -------------------------------------------------------------------------------------------------
# Income and replenishment

def money_view(money_data):
    """Describe the income table as rows of number of houses and income."""
    rows = []
    table = money_data["money"][0]

    for key in table:
        rows.append({"houses": leading_number(key), "value": table[key]})

    return {"rows": rows}


def replenishment_view(config, state: GameState, replenishment_data):
    """Describe how many resources are replenished in each step; the current step is highlighted."""
    rates = replenishment_data[f"{state.number_of_players}_players"]
    step_keys = list(rates.keys())
    steps = []

    for step_key in step_keys:
        classes = ["step-badge"]

        if leading_number(step_key) == state.step:
            classes.append("current")

        steps.append({"label": leading_number(step_key), "classes": classes})

    replenished = []

    for resource in config["resources"]:
        if resource["replenished"]:
            replenished.append(resource)

    rows = []

    for row_index, resource in enumerate(replenished):
        # Rows alternate between dark and light.
        shade = "dark" if row_index % 2 == 0 else "light"
        cells = []

        for step_key in step_keys:
            classes = ["cell"]

            if leading_number(step_key) == state.step:
                classes.append("current")

            cells.append({"value": rates[step_key][0][resource["id"]], "classes": classes})

        rows.append({"icon": resource["icon"], "classes": ["replenishment-row", shade], "cells": cells})

    return {"player_count": state.number_of_players, "steps": steps, "rows": rows}
