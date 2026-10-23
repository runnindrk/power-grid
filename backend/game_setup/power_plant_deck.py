import random


def create_initial_power_plant_setup(plant_definitions, market_size=8, rng=None):
    """Return a sorted starting market and a persisted, ordered draw pile."""
    rng = rng or random
    plug_plants = []
    other_plants = []

    for plant_id, definition in plant_definitions.items():
        if definition["back_of_the_card"] == "plug":
            plug_plants.append(plant_id)
        else:
            other_plants.append(plant_id)

    if len(plug_plants) < market_size + 1:
        raise ValueError("The deck needs one reserved plug and enough plants for the starting market.")

    rng.shuffle(plug_plants)
    rng.shuffle(other_plants)

    next_plant = plug_plants.pop(0)
    market = sorted(plug_plants[:market_size])
    draw_pile = plug_plants[market_size:] + other_plants
    rng.shuffle(draw_pile)
    draw_pile.insert(0, next_plant)

    return market, draw_pile