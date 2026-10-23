from backend.data.files import load_map, load_plant_deck, load_resources, load_settings
from backend.game_setup.power_plant_deck import create_initial_power_plant_setup
from backend.game_setup.regions import create_initial_regions
from backend.game_setup.starting_money import create_initial_player_money
from backend.rules.common.constants import DETERMINING_PLAYER_ORDER
from backend.rules.common.game_state import GameState, default_player_colors


def create_new_game_state(number_of_players, rng=None, player_aliases=None):
    """Build a fresh game entirely from static setup data, never from a saved game."""
    if not isinstance(number_of_players, int) or isinstance(number_of_players, bool):
        raise ValueError("The number of players must be an integer between 2 and 6.")
    if number_of_players < 2 or number_of_players > 6:
        raise ValueError("The number of players must be between 2 and 6.")

    players = [f"p{index}" for index in range(1, number_of_players + 1)]

    if player_aliases is None:
        alias_names = [f"Player {index}" for index in range(1, number_of_players + 1)]
    else:
        if not isinstance(player_aliases, list) or len(player_aliases) != number_of_players:
            raise ValueError("Provide one alias for each player.")

        alias_names = []

        for alias in player_aliases:
            if not isinstance(alias, str):
                raise ValueError("Player aliases must be text.")

            alias = alias.strip()

            if not alias or len(alias) > 40:
                raise ValueError("Player aliases must be 1 to 40 characters.")

            alias_names.append(alias)

        if len({alias.casefold() for alias in alias_names}) != number_of_players:
            raise ValueError("Player aliases must be unique.")

    aliases = dict(zip(players, alias_names))
    settings = load_settings()
    resources = load_resources()["resources"]
    map_data = load_map()
    market, deck, removed = create_initial_power_plant_setup(
        load_plant_deck(), number_of_players, rng=rng,
    )

    return GameState(
        number_of_players=number_of_players,
        regions_chosen=create_initial_regions(map_data, number_of_players, rng),
        rounds_played=0,
        step=1,
        phase=1,
        power_plant_market=market,
        power_plant_deck=deck,
        resource_market={
            resource["id"]: resource["initial_stock"]
            for resource in resources
            if resource["market"]
        },
        player_turn_order=list(players),
        current_player=players[0],
        current_action=DETERMINING_PLAYER_ORDER,
        player_aliases=aliases,
        player_money=create_initial_player_money(players),
        player_power_plants={player: [] for player in players},
        map_houses={
            city: {f"spot_{number}": None for number in range(1, 4)}
            for city, _, _, _ in map_data["cities_positions"]
        },
        pending_houses=[],
        cycles=0,
        player_colors=default_player_colors(aliases, settings["display"]["player_colors"]),
        removed_power_plants=removed,
        game_started=True,
    )