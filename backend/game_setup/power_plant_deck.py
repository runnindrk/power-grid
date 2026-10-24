# -------------------------------------------------------------------------------------------------
# Imports

import random

from backend.data.files import load_plant_removal

# -------------------------------------------------------------------------------------------------
# Shuffle deck

def create_initial_power_plant_setup(plant_definitions, number_of_players, market_size=8, rng=None):
    """Return a sorted market, ordered draw pile, and randomly selected removed plants."""
    rng = rng or random
    plug_plants = []
    other_plants = []
    special_cards = []

    for plant_id, definition in plant_definitions.items():
        if "cost" not in definition:
            special_cards.append(plant_id)
            continue

        if definition["back_of_the_card"] == "plug":
            plug_plants.append(plant_id)
        else:
            other_plants.append(plant_id)

    if len(plug_plants) < market_size + 1:
        raise ValueError("The deck needs one reserved plug and enough plants for the starting market.")

    rng.shuffle(plug_plants)
    rng.shuffle(other_plants)

    removal = load_plant_removal()[f"{number_of_players}_players"]
    removed_plants = []

    for plants, category in ((plug_plants, "plug"), (other_plants, "no_plug")):
        count = removal[category]

        if count < 0 or count > len(plants):
            raise ValueError(f"Cannot remove {count} {category} plants from a deck of {len(plants)}.")

        removed_plants.extend(plants[:count])
        del plants[:count]

    next_plant = plug_plants.pop(0)
    market = sorted(plug_plants[:market_size])
    draw_pile = plug_plants[market_size:] + other_plants
    rng.shuffle(draw_pile)
    draw_pile.insert(0, next_plant)
    draw_pile.extend(special_cards)

    return market, draw_pile, removed_plants


def prepare_initial_power_plant_deck(state, plant_definitions, market_size=8, rng=None):
    """Prepare the plant deck for a new game and store it, including removed plants, in state."""
    market, draw_pile, removed_plants = create_initial_power_plant_setup(
        plant_definitions,
        state.number_of_players,
        market_size=market_size,
        rng=rng,
    )
    state.power_plant_market = market
    state.power_plant_deck = draw_pile
    state.removed_power_plants = removed_plants