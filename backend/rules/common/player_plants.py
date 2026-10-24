# -------------------------------------------------------------------------------------------------
# Imports

from backend.rules.common.constants import FUEL_RESOURCES

# -------------------------------------------------------------------------------------------------
# Plants owned by a player

def new_power_plant(plant_id):
    """Return a plant a player owns: no fuel stored yet and not ready to power."""
    resources = {}

    for resource in FUEL_RESOURCES:
        resources[resource] = 0

    return {"plant_id": plant_id, "resources": resources, "ready_to_power": False}


def find_player_plant(state, player, plant_id):
    """Return the player's plant with the given id, or None if they don't own it."""
    for plant in state.player_power_plants.get(player, []):
        if plant["plant_id"] == plant_id:
            return plant

    return None


def can_power_plant(plant, definition):
    """Return whether a plant has enough compatible fuel to operate once."""
    if definition is None:
        return False

    requirements = {
        resource: definition.get(resource, 0)
        for resource in FUEL_RESOURCES
        if definition.get(resource, 0) > 0
    }
    stored = plant.get("resources", {})

    if definition.get("hybrid"):
        required = max(requirements.values(), default=0)
        return sum(stored.get(resource, 0) for resource in requirements) >= required

    return all(stored.get(resource, 0) >= amount for resource, amount in requirements.items())


def highest_plant_id(state, player):
    """Return the highest plant id the player owns; 0 if they own no plants."""
    highest = 0

    for plant in state.player_power_plants.get(player, []):
        highest = max(highest, plant["plant_id"])

    return highest
