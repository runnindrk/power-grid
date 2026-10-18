# -------------------------------------------------------------------------------------------------
# Imports

from backend.rules.rules import ErrorCode

# -------------------------------------------------------------------------------------------------
# Storage capacity

def storage_capacity(plant_definition, resources):
    """Return how many fuel units a plant can store (twice its fuel need; hybrids use the larger option)."""
    amounts = []

    for resource in resources:
        if resource["fuel"]:
            amount = plant_definition[resource["id"]]
            if amount > 0:
                amounts.append(amount)

    if not amounts:
        return 0

    if plant_definition["hybrid"]:
        return max(amounts) * 2
    return sum(amounts) * 2


def stored_resources(plant):
    """Return one entry per fuel unit stored in the plant, e.g. ['coal', 'coal', 'oil']."""
    stored = []

    for resource in plant["resources"]:
        for _ in range(plant["resources"][resource]):
            stored.append(resource)

    return stored

# -------------------------------------------------------------------------------------------------
# Finding plants

def find_player_plant(state, player, plant_id):
    """Return the player's plant with the given id, or None if they don't own it."""
    for plant in state["player_power_plants"].get(player, []):
        if plant["plant_id"] == plant_id:
            return plant

    return None

# -------------------------------------------------------------------------------------------------
# Moving fuel between plants

def transfer_plant_resource(state, player, source_plant_id, source_slot, target_plant_id, target_slot,
                            plant_definitions, resources):
    """Move one fuel unit between two plants the player owns; returns E_NOT_OKAY if the move is invalid."""
    if source_plant_id == target_plant_id or source_slot < 0 or target_slot < 0:
        return ErrorCode.E_NOT_OKAY

    source = find_player_plant(state, player, source_plant_id)
    target = find_player_plant(state, player, target_plant_id)
    source_definition = plant_definitions.get(source_plant_id)
    target_definition = plant_definitions.get(target_plant_id)
    if source is None or target is None or source_definition is None or target_definition is None:
        return ErrorCode.E_NOT_OKAY

    source_stored = stored_resources(source)
    target_stored = stored_resources(target)
    source_capacity = storage_capacity(source_definition, resources)
    target_capacity = storage_capacity(target_definition, resources)

    if source_slot >= len(source_stored) or len(source_stored) > source_capacity:
        return ErrorCode.E_NOT_OKAY
    if len(target_stored) > target_capacity:
        return ErrorCode.E_NOT_OKAY
    if target_slot >= target_capacity or target_slot < len(target_stored):
        return ErrorCode.E_NOT_OKAY

    resource = source_stored[source_slot]
    source["resources"][resource] -= 1
    target["resources"][resource] = target["resources"].get(resource, 0) + 1

    return ErrorCode.E_OK
