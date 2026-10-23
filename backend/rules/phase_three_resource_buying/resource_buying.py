from backend.rules.common.constants import BUYING_RESOURCES, FUEL_RESOURCES
from backend.rules.common.error_codes import ErrorCode
from backend.rules.common.game_state import GameState
from backend.rules.common.resource_transfer import storage_capacity, stored_resources


def _parse_quantities(requested, resources):
    if not isinstance(requested, dict):
        return None

    buyable = {
        resource["id"]
        for resource in resources
        if resource["buyable"] and resource["market"]
    }

    for resource_id, value in requested.items():
        if resource_id not in buyable and value not in (None, "", 0, "0"):
            return None

    quantities = {}

    for resource_id in buyable:
        value = requested.get(resource_id, 0)

        if value is None or value == "":
            value = 0
        elif isinstance(value, bool):
            return None
        elif isinstance(value, str):
            value = value.strip()

            if not value:
                value = 0
            elif value.isascii() and value.isdigit():
                value = int(value)
            else:
                return None
        elif not isinstance(value, int):
            return None

        if value < 0:
            return None

        quantities[resource_id] = value

    return quantities


def _allocate_resources(state, player, quantities, plant_definitions, resources):
    plants = state.player_power_plants.get(player, [])
    storage_slots = []

    for plant_index, plant in enumerate(plants):
        definition = plant_definitions.get(plant["plant_id"])

        if definition is None:
            continue

        capacity = storage_capacity(definition, resources)
        free_slots = max(0, capacity - len(stored_resources(plant)))
        compatible = {
            resource["id"]
            for resource in resources
            if resource["fuel"] and definition.get(resource["id"], 0) > 0
        }

        for _ in range(free_slots):
            storage_slots.append((plant_index, compatible))

    units = [
        resource_id
        for resource_id in FUEL_RESOURCES
        for _ in range(quantities.get(resource_id, 0))
    ]

    if len(units) > len(storage_slots):
        return None

    ordered_units = sorted(
        range(len(units)),
        key=lambda unit_index: sum(units[unit_index] in allowed for _, allowed in storage_slots),
    )
    slot_units = {}

    def assign_unit(unit_index, visited_slots):
        for slot_index, (_, compatible) in enumerate(storage_slots):
            if units[unit_index] not in compatible or slot_index in visited_slots:
                continue

            visited_slots.add(slot_index)
            previous_unit = slot_units.get(slot_index)

            if previous_unit is None or assign_unit(previous_unit, visited_slots):
                slot_units[slot_index] = unit_index
                return True

        return False

    for unit_index in ordered_units:
        if not assign_unit(unit_index, set()):
            return None

    allocation = [{} for _ in plants]

    for slot_index, unit_index in slot_units.items():
        plant_index = storage_slots[slot_index][0]
        resource_id = units[unit_index]
        allocation[plant_index][resource_id] = allocation[plant_index].get(resource_id, 0) + 1

    return allocation


def _purchase_plan(state, player, requested, plant_definitions, resources, price_scales):
    if state.current_action != BUYING_RESOURCES or player != state.current_player:
        return ErrorCode.E_NOT_OKAY, None

    if state.pending_resource_player not in (None, player):
        return ErrorCode.E_NOT_OKAY, None

    quantities = _parse_quantities(requested, resources)

    if quantities is None:
        return ErrorCode.E_NOT_OKAY, None

    previous = state.pending_resource_purchase if state.pending_resource_player == player else {}
    available_stock = {}
    price = 0

    for resource in resources:
        if not resource["market"] or not resource["buyable"]:
            continue

        resource_id = resource["id"]
        available = state.resource_market.get(resource_id, 0) + previous.get(resource_id, 0)
        quantity = quantities[resource_id]

        if quantity > available:
            return ErrorCode.E_NOT_OKAY, None

        available_stock[resource_id] = available
        price_scale = price_scales[resource["price_scale"]]
        first_slot = resource["capacity"] - available

        for slot in range(first_slot, first_slot + quantity):
            tier = slot // resource["slots_per_tier"]

            if tier >= len(price_scale):
                return ErrorCode.E_NOT_OKAY, None

            price += price_scale[tier]

    if price > state.player_money[player]:
        return ErrorCode.E_NOT_OKAY, None

    allocation = _allocate_resources(state, player, quantities, plant_definitions, resources)

    if allocation is None:
        return ErrorCode.E_NOT_OKAY, None

    return ErrorCode.E_OK, {
        "quantities": quantities,
        "available_stock": available_stock,
        "price": price,
        "allocation": allocation,
    }


def _reserve_plan(state, player, plan):
    for resource_id, available in plan["available_stock"].items():
        state.resource_market[resource_id] = available - plan["quantities"][resource_id]

    state.pending_resource_purchase = plan["quantities"]
    state.pending_resource_player = player if any(plan["quantities"].values()) else None
    state.pending_resource_price = plan["price"]


def quote_resources(state: GameState, player, requested, plant_definitions, resources, price_scales):
    """Reserve a valid selection from the market and return its current price."""
    code, plan = _purchase_plan(state, player, requested, plant_definitions, resources, price_scales)

    if code != ErrorCode.E_OK:
        return code, 0

    _reserve_plan(state, player, plan)

    return ErrorCode.E_OK, plan["price"]


def buy_resources(state: GameState, player, requested, plant_definitions, resources, price_scales):
    """Reserve, pay for, and distribute the selected fuel among compatible owned plants."""
    code, plan = _purchase_plan(state, player, requested, plant_definitions, resources, price_scales)

    if code != ErrorCode.E_OK:
        return code

    _reserve_plan(state, player, plan)
    state.player_money[player] -= plan["price"]

    for plant_index, resource_counts in enumerate(plan["allocation"]):
        plant = state.player_power_plants[player][plant_index]

        for resource_id, count in resource_counts.items():
            plant["resources"][resource_id] = plant["resources"].get(resource_id, 0) + count

    state.pending_resource_purchase = {}
    state.pending_resource_player = None
    state.pending_resource_price = 0

    return ErrorCode.E_OK
