import random
import unittest

from backend.application.game_service import GameService
from backend.data.files import load_map, load_number_of_areas
from backend.data.game_state_store import load_game_state
from backend.game_setup.regions import (
    create_initial_regions,
    prepare_initial_regions,
)
from backend.rules.common.constants import BUILDING_HOUSES
from backend.rules.common.error_codes import ErrorCode
from backend.rules.common.regions import regions_in_play
from backend.views.game_view import build_view


class MapAreasTests(unittest.TestCase):
    def test_area_count_configuration(self):
        self.assertEqual(load_number_of_areas(), {
            "2_players": 3,
            "3_players": 3,
            "4_players": 4,
            "5_players": 5,
            "6_players": 5,
        })

    def test_active_region_count_follows_player_count(self):
        state = load_game_state()
        state.regions_chosen = ["green", "orange", "red", "yellow", "blue", "purple"]

        for number_of_players, expected_count in ((2, 3), (3, 3), (4, 4), (5, 5), (6, 5)):
            with self.subTest(number_of_players=number_of_players):
                state.number_of_players = number_of_players
                self.assertEqual(
                    len(regions_in_play(state, load_number_of_areas())),
                    expected_count,
                )

    def test_setup_randomizes_connected_regions_for_each_player_count(self):
        map_data = load_map()

        for number_of_players in range(2, 7):
            with self.subTest(number_of_players=number_of_players):
                chosen = create_initial_regions(
                    map_data,
                    number_of_players,
                    rng=random.Random(number_of_players),
                )

                self.assertEqual(
                    len(chosen),
                    load_number_of_areas()[f"{number_of_players}_players"],
                )
                self.assertTrue(self.regions_are_connected(map_data, chosen))

    def test_setup_randomizes_between_seeds_and_stores_selection(self):
        map_data = load_map()
        first = create_initial_regions(map_data, 4, rng=random.Random(1))
        second = create_initial_regions(map_data, 4, rng=random.Random(2))
        state = load_game_state()

        prepare_initial_regions(state, map_data, rng=random.Random(1))

        self.assertNotEqual(first, second)
        self.assertEqual(state.regions_chosen, first)

    def test_service_construction_does_not_randomize_saved_state(self):
        state = load_game_state()
        original = list(state.regions_chosen)
        original_order = list(state.player_turn_order)
        original_action = state.current_action
        GameService(state, lambda saved: None, rng=random.Random(17))

        self.assertEqual(state.regions_chosen, original)
        self.assertEqual(state.player_turn_order, original_order)
        self.assertEqual(state.current_action, original_action)

    @staticmethod
    def regions_are_connected(map_data, chosen):
        cities = map_data["cities_positions"]
        region_by_city = {city[0]: city[1].casefold() for city in cities}
        matrix = [
            [value for value in row if not isinstance(value, str)]
            for row in map_data["connection_matrix"]
        ]
        adjacency = {region: set() for region in chosen}

        for first in range(len(matrix)):
            for second in range(first + 1, len(matrix)):
                cost = matrix[first][second]

                if cost is None:
                    cost = matrix[second][first]

                if cost is None:
                    continue

                first_region = region_by_city[cities[first][0]]
                second_region = region_by_city[cities[second][0]]

                if first_region in adjacency and second_region in adjacency:
                    adjacency[first_region].add(second_region)
                    adjacency[second_region].add(first_region)

        visited = set()
        frontier = [chosen[0]]

        while frontier:
            region = frontier.pop()

            if region in visited:
                continue

            visited.add(region)
            frontier.extend(adjacency[region] - visited)

        return visited == set(chosen)

    def test_map_view_disables_cities_outside_chosen_regions(self):
        state = load_game_state()
        active_regions = regions_in_play(state, load_number_of_areas())
        cities = build_view(state)["map"]["cities"]

        for city in cities:
            with self.subTest(city=city["name"]):
                self.assertEqual(city["active"], city["region"].casefold() in active_regions)

                if not city["active"]:
                    self.assertTrue(city["aria_disabled"])
                    self.assertTrue(all(spot["aria_disabled"] for spot in city["spots"]))

    def test_house_spots_reject_inactive_regions_and_allow_active_regions(self):
        state = load_game_state()
        state.current_action = BUILDING_HOUSES
        active_regions = regions_in_play(state, load_number_of_areas())
        city_regions = {
            name: region.casefold()
            for name, region, _, _ in load_map()["cities_positions"]
        }
        service = GameService(state, lambda saved: None)

        inactive_city = next(
            city for city, region in city_regions.items()
            if region not in active_regions
            and any(owner is None for owner in state.map_houses[city].values())
        )
        inactive_spot = next(
            spot for spot, owner in state.map_houses[inactive_city].items()
            if owner is None
        )
        active_city = next(
            city for city, region in city_regions.items()
            if region in active_regions
            and any(owner is None for owner in state.map_houses[city].values())
        )
        active_spot = next(
            spot for spot, owner in state.map_houses[active_city].items()
            if owner is None
        )

        self.assertEqual(service.toggle_house_spot(inactive_city, inactive_spot), ErrorCode.E_NOT_OKAY)
        self.assertEqual(service.toggle_house_spot(active_city, active_spot), ErrorCode.E_OK)


if __name__ == "__main__":
    unittest.main()