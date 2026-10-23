# -------------------------------------------------------------------------------------------------
# Imports

from backend.rules.common.game_state import GameState
from backend.rules.phase_four_building_houses.building_houses import quote_houses
from backend.rules.phase_two_auction.auction import highest_active_bid
from backend.views.plant_view import owned_plant_card

# -------------------------------------------------------------------------------------------------
# Player labels and colors

def player_label(state, player):
    """Return the alias of a player, or the player id if there is no alias."""
    return state["player_aliases"].get(player, player)


def player_color(config, state, player):
    """Return the player's persistent color, independent of turn order."""
    player_colors = state.get("player_colors", {})
    if player in player_colors:
        return player_colors[player]

    # Older saves may not have stored colors yet; use stable roster order once.
    palette = config["display"]["player_colors"]
    index = list(state["player_aliases"]).index(player)
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
            card = owned_plant_card(config, deck.get(plant["plant_id"]), player, plant)
            card["discardable"] = (
                game_state.current_action == "discard_power_plant"
                and game_state.current_player == player
            )
            if card["discardable"]:
                card["classes"].append("discardable")
                card["discard_player"] = player
            slots.append(card)
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
    """Describe the house-buying button, its price summary, and disabled state."""
    text = config["text"]
    count = len(state["pending_houses"])

    result = {
        "label": text["buy_houses"],
        "aria_label": f"Buy houses for {player_label(state, player)}",
        "buy_disabled": True,
    }

    if player != state["current_player"]:
        result["total"] = text["waiting_for_turn"]
    elif game_state.current_action != "building_houses":
        result["total"] = text["house_prompt"]
    elif count == 0:
        result["total"] = text["house_prompt"]
        result["buy_disabled"] = False
    else:
        price = quote_houses(game_state, player, state["pending_houses"])
        result["total"] = text["house_summary"].format(count=count, price=price)
        result["buy_disabled"] = False

    return result


def resource_buy_view(config, state, player, game_state):
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
        "disabled": (
            player != state["current_player"]
            or game_state.current_action != "buying_resources"
        ),
        "rows": rows,
    }


def bid_view(config, state, player, game_state):
    """Describe the auction bid panel of a player."""
    alias = player_label(state, player)
    bidding = game_state.current_action == "power_plant_bidding"
    highest_bid = highest_active_bid(game_state)
    minimum_bid = highest_bid + 1 if bidding else config["rules"]["min_bid"]

    return {
        "min": minimum_bid,
        "max": state["player_money"][player],
        "value": minimum_bid,
        "status": f"Highest bid: {highest_bid}" if highest_bid else config["text"]["no_bid_yet"],
        "disabled": player != state["current_player"] or not bidding,
        "pass_disabled": (
            player != state["current_player"]
            or game_state.current_action not in ("power_plant_auction", "power_plant_bidding")
        ),
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
        "is_current_player": player == state["current_player"],
        "can_power": (
            player == state["current_player"]
            and game_state.current_action == "bureaucracy"
        ),
        "label": alias,
        "aria_label": f"Player {alias}",
        "color": player_color(config, state, player),
        "network": {
            "count": count_network_houses(state, player),
            "label": config["text"]["in_network"],
        },
        "money": {"value": money, "label": config["text"]["money_format"].format(money=money)},
        "bid": bid_view(config, state, player, game_state),
        "resource_buy": resource_buy_view(config, state, player, game_state),
        "house_purchase": house_purchase_view(config, state, player, game_state),
        "plant_slots": plant_slots(config, state, player, deck, game_state),
    }
