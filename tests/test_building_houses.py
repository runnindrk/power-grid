import random
import unittest

from backend.application.game_service import GameService
from backend.data.files import load_settings
from backend.data.game_state_store import load_game_state
from backend.game_setup.new_game import create_new_game_state
from backend.rules.common.constants import BUILDING_HOUSES
from backend.rules.common.error_codes import ErrorCode
from backend.rules.phase_four_building_houses.building_houses import buy_houses, quote_houses
from backend.server.app import create_app
from backend.views.game_view import build_view


class BuildingHouseRuleTests(unittest.TestCase):
    def setUp(self):
        self.state = load_game_state()
        self.player = self.state.player_turn_order[0]
        self.state.step = 3
        self.state.player_money[self.player] = 100
        self.state.map_houses = {
            city: {"spot_1": None, "spot_2": None, "spot_3": None}
            for city in ("A", "B", "C", "D")
        }
        self.map_data = {
            "cities_positions": [
                ["A", "North", 0, 0],
                ["B", "North", 1, 0],
                ["C", "North", 2, 0],
                ["D", "North", 3, 0],
            ],
            "connection_matrix": [
                [0, "A_Current_Row", 4, "B", None, "C", None, "D"],
                [4, "A", 0, "B_Current_Row", 5, "C", None, "D"],
                [None, "A", 5, "B", 0, "C_Current_Row", 3, "D"],
                [None, "A", None, "B", 3, "C", 0, "D_Current_Row"],
            ],
        }
        self.active_regions = {"north"}
        self.spot_costs = {"spot_1": 10, "spot_2": 15, "spot_3": 20}

    def test_new_game_service_quotes_and_buys_connected_houses(self):
        state = create_new_game_state(4, rng=random.Random(31))
        state.regions_chosen = ["green", "orange", "red", "yellow"]
        state.step = 3
        state.current_action = BUILDING_HOUSES
        player = state.player_turn_order[0]
        state.current_player = player
        service = GameService(state, lambda saved: None)
        client = create_app(service).test_client()

        self.assertEqual(service.toggle_house_spot("Flensburg", "spot_1"), ErrorCode.E_OK)
        self.assertEqual(service.toggle_house_spot("Kiel", "spot_2"), ErrorCode.E_OK)

        player_view = next(row for row in client.get("/api/view").get_json()["players"] if row["player"] == player)
        self.assertEqual(player_view["house_purchase"]["total"], "2 · $29")
        self.assertEqual(client.post("/api/buy-houses", json={"player": player}).status_code, 200)
        self.assertEqual(state.player_money[player], 21)
        self.assertEqual(state.map_houses["Flensburg"]["spot_1"], player)
        self.assertEqual(state.map_houses["Kiel"]["spot_2"], player)
        state.current_player = player
        self.assertEqual(service.toggle_house_spot("Kiel", "spot_3"), ErrorCode.E_NOT_OKAY)

    def test_step_unlocks_are_visible_in_the_map_view(self):
        state = create_new_game_state(4, rng=random.Random(31))
        state.regions_chosen = ["green", "orange", "red", "yellow"]

        for step, expected_availability in ((1, [True, False, False]), (2, [True, True, False]), (3, [True, True, True])):
            with self.subTest(step=step):
                state.step = step
                spots = next(
                    city["spots"]
                    for city in build_view(state)["map"]["cities"]
                    if city["name"] == "Flensburg"
                )
                self.assertEqual([not spot["aria_disabled"] for spot in spots], expected_availability)

    def test_first_house_only_costs_its_spot_and_next_house_counts_multi_edge_route(self):
        placements = [
            {"city": "A", "spot": "spot_1"},
            {"city": "D", "spot": "spot_2"},
        ]

        self.assertEqual(
            quote_houses(self.state, self.player, placements, self.map_data, self.active_regions, self.spot_costs),
            37,
        )

    def test_existing_network_is_used_as_a_zero_extra_first_connection(self):
        self.state.map_houses["A"]["spot_1"] = self.player
        placements = [{"city": "D", "spot": "spot_1"}]

        self.assertEqual(
            quote_houses(self.state, self.player, placements, self.map_data, self.active_regions, self.spot_costs),
            22,
        )

    def test_connection_uses_only_the_cheapest_single_route_from_network(self):
        self.state.map_houses["A"]["spot_1"] = self.player
        self.state.map_houses["B"]["spot_1"] = self.player
        self.map_data["connection_matrix"][0][6] = 7
        placements = [{"city": "D", "spot": "spot_1"}]

        self.assertEqual(
            quote_houses(self.state, self.player, placements, self.map_data, self.active_regions, self.spot_costs),
            17,
        )

    def test_spots_unlock_by_step_and_player_can_only_have_one_house_per_city(self):
        self.state.step = 1
        locked = [{"city": "A", "spot": "spot_2"}]
        self.assertIsNone(
            quote_houses(self.state, self.player, locked, self.map_data, self.active_regions, self.spot_costs),
        )

        duplicate_city = [
            {"city": "A", "spot": "spot_1"},
            {"city": "A", "spot": "spot_2"},
        ]
        self.state.step = 3
        self.assertIsNone(
            quote_houses(
                self.state, self.player, duplicate_city, self.map_data, self.active_regions, self.spot_costs,
            ),
        )

    def test_buy_charges_once_and_places_all_valid_houses(self):
        placements = [
            {"city": "A", "spot": "spot_1"},
            {"city": "D", "spot": "spot_2"},
        ]
        self.state.pending_houses = list(placements)

        self.assertEqual(
            buy_houses(self.state, self.player, placements, self.map_data, self.active_regions, self.spot_costs),
            ErrorCode.E_OK,
        )
        self.assertEqual(self.state.player_money[self.player], 63)
        self.assertEqual(self.state.map_houses["A"]["spot_1"], self.player)
        self.assertEqual(self.state.map_houses["D"]["spot_2"], self.player)
        self.assertFalse(self.state.pending_houses)

    def test_unaffordable_purchase_changes_nothing(self):
        placements = [{"city": "A", "spot": "spot_1"}]
        self.state.player_money[self.player] = 9
        self.state.pending_houses = list(placements)

        self.assertEqual(
            buy_houses(self.state, self.player, placements, self.map_data, self.active_regions, self.spot_costs),
            ErrorCode.E_NOT_OKAY,
        )
        self.assertIsNone(self.state.map_houses["A"]["spot_1"])
        self.assertEqual(self.state.player_money[self.player], 9)
        self.assertEqual(self.state.pending_houses, placements)


if __name__ == "__main__":
    unittest.main()