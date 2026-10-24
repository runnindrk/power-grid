# -------------------------------------------------------------------------------------------------
# Imports

from backend.rules.common.constants import FUEL_RESOURCES
from backend.rules.common.error_codes import ErrorCode
from backend.rules.common.game_state import GameState
from backend.rules.common.player_houses import count_houses
from backend.rules.common.player_plants import can_power_plant
from backend.rules.common.resource_transfer import stored_resources

# -------------------------------------------------------------------------------------------------
# Phase five: bureaucracy

def _consume_fuel(plant, definition):
    if not can_power_plant(plant, definition):
        return False

    requirements = {
        resource: definition.get(resource, 0)
        for resource in FUEL_RESOURCES
        if definition.get(resource, 0) > 0
    }
    stored = plant["resources"]

    if definition.get("hybrid"):
        remaining = max(requirements.values(), default=0)
        consumed_resources = []

        for resource in stored_resources(plant):
            if resource not in requirements:
                continue

            consumed_resources.append(resource)
            remaining -= 1

            if remaining == 0:
                break

        for resource in consumed_resources:
            stored[resource] -= 1

        return True

    if any(stored.get(resource, 0) < amount for resource, amount in requirements.items()):
        return False

    for resource, amount in requirements.items():
        stored[resource] = stored.get(resource, 0) - amount

    return True


def bureaucracy(state: GameState, player, plant_definitions, income_table):
    """Power ready plants with sufficient fuel, cap production at the network, and pay income."""
    powered_houses = 0

    for plant in state.player_power_plants.get(player, []):
        if not plant.get("ready_to_power", False):
            continue

        definition = plant_definitions.get(plant["plant_id"])

        if definition is not None and _consume_fuel(plant, definition):
            powered_houses += definition["houses"]

        plant["ready_to_power"] = False

    powered_houses = min(powered_houses, count_houses(state, player))
    maximum_paid_houses = max(int(key.split("_", 1)[0]) for key in income_table)
    payout = income_table[f"{min(powered_houses, maximum_paid_houses):02}_houses"]
    state.player_money[player] += payout

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
