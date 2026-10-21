# -------------------------------------------------------------------------------------------------
# Imports

from backend.rules.rules import quote_houses
from backend.rules.game_state import GameState
from backend.views.plant_view import owned_plant_card

# -------------------------------------------------------------------------------------------------
# Player labels and colors

def player_label(state, player):
    """Return the alias of a player, or the player id if there is no alias."""
    return state["player_aliases"].get(player, player)


def player_color(config, state, player):
    """Return the color of a player, chosen by their position in the turn order."""
    palette = config["display"]["player_colors"]
    index = state["player_turn_order"].index(player)

    return palette[index % len(palette)]


def count_network_houses(state, player):
    """Return how many houses the player has on the map."""
    count = 0

    for city in state["map_houses"]:
        for spot in state["map_houses"][city]:
            if state["map_houses"][city][spot] == player:
                count += 1

    return count

# -------------------------------------------------------------------------------------------------
# Plant slots

def plant_slots(config, state, player, deck, game_state):
    """Return the player's fixed plant slots: their plants first, then empty slots."""
    alias = player_label(state, player)
    owned = state["player_power_plants"][player]
    slots = []

    for slot_index in range(config["rules"]["plant_slots_per_player"]):
        if slot_index < len(owned):
            plant = owned[slot_index]
            slots.append(owned_plant_card(config, deck.get(plant["plant_id"]), player, plant))
        else:
            slots.append({
                "empty": True,
                "classes": ["player-plant-slot", "empty"],
                "label": config["text"]["empty_plant_slot"],
                "aria_label": f"Empty power plant slot {slot_index + 1} for {alias}",
            })

    return slots

# -------------------------------------------------------------------------------------------------
# Player controls

def house_purchase_view(config, state, player, game_state):
    """Describe the house buying button: its label, its summary (houses and price) and whether it is disabled."""
    text = config["text"]
    count = len(state["pending_houses"])

    result = {
        "label": text["buy_houses"],
        "aria_label": f"Buy houses for {player_label(state, player)}",
        "buy_disabled": True,
    }

    if player != state["current_player"]:
        result["total"] = text["waiting_for_turn"]
    elif count == 0:
        result["total"] = text["house_prompt"]
    else:
        price = quote_houses(game_state, player, state["pending_houses"])
        result["total"] = text["house_summary"].format(count=count, price=price)
        result["buy_disabled"] = False

    return result


def resource_buy_view(config, state, player):
    """Describe the resource buying panel: one row for each buyable resource."""
    alias = player_label(state, player)
    rows = []

    for resource in config["resources"]:
        if resource["buyable"]:
            label = resource["market_label"]

            rows.append({
                "resource": resource["id"],
                "label": label,
                "icon": resource["icon"],
                "classes": ["resource-buy-row", "resource-" + resource["id"]],
                "aria_label": f"{label} quantity for {alias}",
            })

    return {
        "aria_label": f"Buy resources for {alias}",
        "buy_aria_label": f"Buy selected resources for {alias}",
        "price_label": config["text"]["price_format"].format(price=0),
        "rows": rows,
    }


def bid_view(config, state, player):
    """Describe the auction bid panel of a player."""
    alias = player_label(state, player)

    return {
        "min": config["rules"]["min_bid"],
        "max": state["player_money"][player],
        "value": config["rules"]["min_bid"],
        "status": config["text"]["no_bid_yet"],
        "disabled": False,
        "aria_label": f"Power plant bid for {alias}",
        "input_aria_label": f"Bid amount for {alias}",
    }

# -------------------------------------------------------------------------------------------------
# Player row

def player_row(config, state, player, deck, game_state: GameState):
    """Describe one row of the player board: money, network, controls and plant slots."""
    alias = player_label(state, player)
    money = state["player_money"][player]

    return {
        "player": player,
        "label": alias,
        "aria_label": f"Player {alias}",
        "color": player_color(config, state, player),
        "network": {
            "count": count_network_houses(state, player),
            "label": config["text"]["in_network"],
        },
        "money": {"value": money, "label": config["text"]["money_format"].format(money=money)},
        "bid": bid_view(config, state, player),
        "resource_buy": resource_buy_view(config, state, player),
        "house_purchase": house_purchase_view(config, state, player, game_state),
        "plant_slots": plant_slots(config, state, player, deck, game_state),
    }
