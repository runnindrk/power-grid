# -------------------------------------------------------------------------------------------------
# Imports

from backend.rules.common.resource_transfer import storage_capacity, stored_resources

# -------------------------------------------------------------------------------------------------
# Fuel

def resource_label(config, resource_id):
    """Return the label of a resource, or its id if the resource is not in the resource list."""
    for resource in config["resources"]:
        if resource["id"] == resource_id:
            return resource["label"]

    return resource_id


def fuel_view(config, definition):
    """Describe the fuel a plant burns, joined by 'or' for hybrid plants and '+' for the others."""
    fuels = []

    for resource in config["resources"]:
        if resource["fuel"] and definition[resource["id"]] > 0:
            fuels.append(resource)

    items = []

    for index in range(len(fuels)):
        resource = fuels[index]
        join = None

        if index > 0 and definition["hybrid"]:
            join = "or"
        elif index > 0:
            join = "+"

        amount = definition[resource["id"]]

        items.append({
            "join": join,
            "classes": ["fuel-item", "fuel-" + resource["id"]],
            "label": resource["label"],
            "icon": resource["icon"],
            "amount": amount,
            "aria_label": f"{amount} {resource['label']}",
        })

    classes = ["fuel-options"]

    if definition["hybrid"]:
        classes.append("hybrid")

    empty_label = None

    if not items:
        empty_label = config["text"]["no_fuel"]

    return {"empty_label": empty_label, "classes": classes, "items": items}

# -------------------------------------------------------------------------------------------------
# Fuel storage

def storage_view(config, definition, player, plant):
    """Describe the fuel storage slots of a plant (filled or empty); None if the plant stores no fuel."""
    capacity = storage_capacity(definition, config["resources"])

    if capacity == 0:
        return None

    stored = stored_resources(plant)
    slots = []

    for slot_index in range(capacity):
        classes = ["plant-storage-slot"]
        title = config["text"]["empty_storage"]
        draggable = False

        if slot_index < len(stored):
            resource = stored[slot_index]
            classes.append("filled")
            classes.append("fuel-" + resource)
            title = config["text"]["stored_title"].format(resource=resource_label(config, resource))
            draggable = True

        slots.append({
            "classes": classes,
            "draggable": draggable,
            "title": title,
            "drag": {"player": player, "source_plant_id": plant["plant_id"], "source_slot": slot_index},
            "drop": {"target_plant_id": plant["plant_id"], "target_slot": slot_index},
        })

    return {"aria_label": f"{capacity} resource storage spaces", "slots": slots}

# -------------------------------------------------------------------------------------------------
# Plant cards

def plant_card(config, plant_id, definition, is_owned):
    """Describe a power plant card; definition is None if the plant is not in the deck."""
    text = config["text"]
    classes = ["power-plant-card"]

    if definition is not None and definition["special"]:
        classes.append("special")

    if is_owned:
        classes.append("player-owned-plant")

    if definition is None:
        return {
            "plant_id": plant_id,
            "classes": classes,
            "kind": text["plant_kind"],
            "aria_label": f"Power plant {plant_id}, details unavailable",
            "unavailable": True,
        }

    kind = text["plant_kind"]

    if definition["special"]:
        kind = text["special_kind"]

    return {
        "plant_id": plant_id,
        "classes": classes,
        "kind": kind,
        "aria_label": f"Power plant {plant_id}, powers {definition['houses']} cities",
        "unavailable": False,
        "houses": definition["houses"],
        "fuel": fuel_view(config, definition),
        "storage": None,
        "ready_to_power": None,
    }


def owned_plant_card(config, definition, player, plant):
    """Describe a plant on a player board: the plant card plus its storage and ready-to-power button."""
    card = plant_card(config, plant["plant_id"], definition, True)

    if definition is None:
        return card

    card["storage"] = storage_view(config, definition, player, plant)
    card["ready_to_power"] = {
        "player_id": player,
        "plant_id": plant["plant_id"],
        "pressed": plant["ready_to_power"],
    }

    return card
