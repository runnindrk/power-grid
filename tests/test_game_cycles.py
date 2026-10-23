import random
import unittest
from copy import deepcopy

from backend.application.game_service import GameService
from backend.data.game_state_store import load_game_state
from backend.rules.common.error_codes import ErrorCode
from backend.rules.phase_one_turn_order.initial_order import determine_initial_order
from backend.server.main import app


class GameCycleTests(unittest.TestCase):
    # Loading a phase-one save randomizes order once and starts the auction.
    def test_startup_determines_order_and_enters_phase_two(self):
        state = load_game_state()
        self.assertEqual(state.phase, 1)
        self.assertEqual(state.current_action, "determining_player_order")
        original_players = sorted(state.player_turn_order)
        service = GameService(state, lambda saved: None, rng=random.Random(7))

        self.assertEqual(state.phase, 2)
        self.assertEqual(state.current_action, "power_plant_auction")
        self.assertEqual(state.current_player, state.player_turn_order[0])
        self.assertEqual(sorted(state.player_turn_order), original_players)
        self.assertEqual(state.cycles, 0)

    # The first auction ends by ordering the resource phase by highest plant.
    def test_cycle_zero_auction_handoff_orders_by_highest_plant(self):
        state = deepcopy(load_game_state())
        p1, p2, p3, p4 = state.player_turn_order
        state.cycles = 0
        state.current_action = "power_plant_auction"
        state.current_player = p1
        state.player_power_plants = {
            p1: [{"plant_id": 22}],
            p2: [{"plant_id": 33}],
            p3: [{"plant_id": 10}],
            p4: [],
        }
        service = GameService(state, lambda saved: None)

        for _ in state.player_turn_order:
            self.assertEqual(service.pass_bid(state.current_player), ErrorCode.E_OK)

        self.assertEqual(state.player_turn_order, [p2, p1, p3, p4])
        self.assertEqual(state.phase, 3)
        self.assertEqual(state.current_action, "buying_resources")
        self.assertEqual(state.current_player, p2)

    # Every later cycle orders by houses, then highest plant, preserving exact ties.
    def test_cycles_after_first_order_by_houses_then_highest_plant(self):
        state = deepcopy(load_game_state())
        p1, p2, p3, p4 = state.player_turn_order
        state.cycles = 1
        state.current_action = "determining_player_order"
        state.player_power_plants = {
            p1: [{"plant_id": 15}],
            p2: [{"plant_id": 21}],
            p3: [{"plant_id": 5}],
            p4: [{"plant_id": 50}],
        }
        for city in state.map_houses.values():
            for spot in city:
                city[spot] = None
        state.map_houses["Flensburg"]["spot_1"] = p1
        state.map_houses["Kiel"]["spot_1"] = p1
        state.map_houses["Hamburg"]["spot_1"] = p2
        state.map_houses["Cuxhaven"]["spot_1"] = p2
        state.map_houses["Bremen"]["spot_1"] = p3
        state.map_houses["Wilhelmshaven"]["spot_1"] = p3
        state.map_houses["Hannover"]["spot_1"] = p3

        self.assertEqual(determine_initial_order(state), ErrorCode.E_OK)
        self.assertEqual(state.player_turn_order, [p3, p2, p1, p4])
        self.assertEqual(state.current_player, p3)

    # Phases one through five complete in order before cycles increments.
    def test_complete_five_phase_cycle_increments_counter_and_resets_order(self):
        state = load_game_state()
        self.assertEqual(state.phase, 1)
        self.assertEqual(state.current_action, "determining_player_order")
        service = GameService(state, lambda saved: None, rng=random.Random(11))

        self.assertEqual(state.phase, 2)
        self.assertEqual(state.current_action, "power_plant_auction")
        self.assertEqual(state.cycles, 0)

        for _ in state.player_turn_order:
            self.assertEqual(service.pass_bid(state.current_player), ErrorCode.E_OK)

        self.assertEqual(state.phase, 3)
        self.assertEqual(state.current_action, "buying_resources")

        for _ in state.player_turn_order:
            self.assertEqual(service.buy_resources(state.current_player, {}), ErrorCode.E_OK)

        self.assertEqual(state.phase, 4)
        self.assertEqual(state.current_action, "building_houses")

        for _ in state.player_turn_order:
            self.assertEqual(service.buy_houses(state.current_player), ErrorCode.E_OK)

        self.assertEqual(state.phase, 5)
        self.assertEqual(state.current_action, "bureaucracy")

        for _ in state.player_turn_order:
            self.assertEqual(service.bureaucracy(state.current_player), ErrorCode.E_OK)

        self.assertEqual(state.cycles, 1)
        self.assertEqual(state.phase, 2)
        self.assertEqual(state.current_action, "power_plant_auction")
        self.assertEqual(state.current_player, state.player_turn_order[0])
        self.assertFalse(state.phase_finished_players)

    # The header view exposes the cycle counter for the UI.
    def test_cycle_count_is_in_header_view(self):
        original_service = app.config["game_service"]
        state = deepcopy(original_service.snapshot())
        state.cycles = 3
        app.config["game_service"] = GameService(state, lambda saved: None)

        try:
            header = app.test_client().get("/api/view").get_json()["header"]
            self.assertEqual(header["cycles"], 3)
        finally:
            app.config["game_service"] = original_service


if __name__ == "__main__":
    unittest.main()