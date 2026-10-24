# -------------------------------------------------------------------------------------------------
# Imports

from backend.rules.common.error_codes import ErrorCode
from backend.rules.common.game_state import GameState

# -------------------------------------------------------------------------------------------------
# Phase five: bureaucracy

def bureaucracy(state: GameState, player):
    """Placeholder: power plants and pay income."""
    return ErrorCode.E_OK


def finish_bureaucracy(state: GameState, replenishment_data, resources):
    """Replenish the resource market and remove the highest plant during Steps 1 and 2."""
    replenishment = replenishment_data[f"{state.number_of_players}_players"][f"{state.step}_step"][0]

    for resource in resources:
        if not resource["market"] or not resource["replenished"]:
            continue

        resource_id = resource["id"]
        amount = replenishment.get(resource_id, 0)
        stock = state.resource_market.get(resource_id, 0)
        state.resource_market[resource_id] = min(resource["capacity"], stock + amount)

    if state.step in (1, 2) and state.power_plant_market:
        highest_plant = max(state.power_plant_market)
        state.power_plant_market.remove(highest_plant)
        state.power_plant_deck.append(highest_plant)
