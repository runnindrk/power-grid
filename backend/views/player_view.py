# -------------------------------------------------------------------------------------------------
# Imports

from backend.rules.common.constants import (
    BUILDING_HOUSES,
    BUREAUCRACY,
    BUYING_RESOURCES,
    DISCARD_POWER_PLANT,
    POWER_PLANT_AUCTION,
    POWER_PLANT_BIDDING,
)
from backend.rules.common.game_state import GameState, default_player_colors
from backend.rules.common.player_houses import count_houses
from backend.rules.phase_four_building_houses.building_houses import quote_houses
from backend.rules.phase_two_auction.auction import highest_active_bid
from backend.views.plant_view import owned_plant_card

# -------------------------------------------------------------------------------------------------
# Player labels and colors

def player_label(state: GameState, player):
    """Return the alias of a player, or the player id if there is no alias."""
    return state.player_aliases.get(player, player)


def player_color(config, state: GameState, player):
    """Return the persistent color of a player; it does not change with the turn order."""
    if player in state.player_colors:
        return state.player_colors[player]

    # Older saves have no colors; use the roster order, which never changes.
    palette = config["display"]["player_colors"]

    return default_player_colors(state.player_aliases, palette)[player]

# -------------------------------------------------------------------------------------------------
# Plant slots

def plant_slots(config, state: GameState, player, deck):
    """Return the fixed plant slots of a player: their plants first, then the empty slots."""
    alias = player_label(state, player)
    owned = state.player_power_plants[player]
    slots = []

    for slot_index in range(config["rules"]["plant_slots_per_player"]):
        if slot_index >= len(owned):
            slots.append({
                "empty": True,
                "classes": ["player-plant-slot", "empty"],
                "label": config["text"]["empty_plant_slot"],
                "aria_label": f"Empty power plant slot {slot_index + 1} for {alias}",
            })
            continue

        plant = owned[slot_index]
        card = owned_plant_card(config, deck.get(plant["plant_id"]), player, plant)

        # The winner of a plant with full slots must click a plant to discard.
        card["discardable"] = (
            state.current_action == DISCARD_POWER_PLANT
            and state.current_player == player
        )

        if card["discardable"]:
            card["classes"].append("discardable")
            card["discard_player"] = player

        slots.append(card)

    return slots

# -------------------------------------------------------------------------------------------------
# Player controls

def house_purchase_view(config, state: GameState, player):
    """Describe the house buying button: its price summary and whether it is disabled."""
    text = config["text"]
    count = len(state.pending_houses)

    result = {
        "label": text["buy_houses"],
        "aria_label": f"Buy houses for {player_label(state, player)}",
        "buy_disabled": True,
    }

    if player != state.current_player:
        result["total"] = text["waiting_for_turn"]
    elif state.current_action != BUILDING_HOUSES:
        result["total"] = text["house_prompt"]
    elif count == 0:
        result["total"] = text["house_prompt"]
        result["buy_disabled"] = False
    else:
        price = quote_houses(state, player, state.pending_houses)
        result["total"] = text["house_summary"].format(count=count, price=price)
        result["buy_disabled"] = False

    return result


def resource_buy_view(config, state: GameState, player):
    """Describe the resource buying panel: one row for each buyable resource."""
    alias = player_label(state, player)
    text = config["text"]
    rows = []

    for resource in config["resources"]:
        if not resource["buyable"]:
            continue

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
        "buy_label": text["buy_button"],
        "price_label": text["price_format"].format(price=0),
        "disabled": player != state.current_player or state.current_action != BUYING_RESOURCES,
        "rows": rows,
    }


def bid_view(config, state: GameState, player):
    """Describe the bid panel of a player."""
    alias = player_label(state, player)
    text = config["text"]
    is_current = player == state.current_player
    is_bidding = state.current_action == POWER_PLANT_BIDDING
    selector_cannot_pass = state.cycles == 0 and is_bidding and player == state.auction_starter
    highest_bid = highest_active_bid(state)

    # During the bidding a bid must be higher than the highest one; the opening bid is the plant price.
    minimum_bid = config["rules"]["min_bid"]

    if is_bidding:
        minimum_bid = highest_bid + 1

    status = text["no_bid_yet"]

    if highest_bid:
        status = text["highest_bid"].format(bid=highest_bid)

    return {
        "min": minimum_bid,
        "max": state.player_money[player],
        "value": minimum_bid,
        "status": status,
        "amount_label": text["bid_amount"],
        "bid_label": text["bid_button"],
        "pass_label": text["pass_button"],
        "disabled": not is_current or not is_bidding,
        "pass_disabled": (
            not is_current
            or state.current_action not in (POWER_PLANT_AUCTION, POWER_PLANT_BIDDING)
            or selector_cannot_pass
        ),
        "aria_label": f"Power plant bid for {alias}",
        "input_aria_label": f"Bid amount for {alias}",
    }

# -------------------------------------------------------------------------------------------------
# Player row

def player_row(config, state: GameState, player, deck):
    """Describe one row of the player board: money, network, controls and plant slots."""
    alias = player_label(state, player)
    money = state.player_money[player]
    is_current = player == state.current_player

    return {
        "player": player,
        "is_current_player": is_current,
        "can_power": is_current and state.current_action == BUREAUCRACY,
        "label": alias,
        "aria_label": f"Player {alias}",
        "color": player_color(config, state, player),
        "network": {
            "count": count_houses(state, player),
            "label": config["text"]["in_network"],
        },
        "money": {"value": money, "label": config["text"]["money_format"].format(money=money)},
        "bid": bid_view(config, state, player),
        "resource_buy": resource_buy_view(config, state, player),
        "house_purchase": house_purchase_view(config, state, player),
        "plant_slots": plant_slots(config, state, player, deck),
    }
