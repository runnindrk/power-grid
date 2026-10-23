import random
import unittest

from backend.data.game_state_store import load_game_state
from backend.rules.common.constants import (
    BUILDING_HOUSES,
    BUREAUCRACY,
    BUYING_RESOURCES,
    DETERMINING_PLAYER_ORDER,
    POWER_PLANT_AUCTION,
)
from backend.rules.common.error_codes import ErrorCode
from backend.rules.phase_one_turn_order.initial_order import determine_initial_order
from backend.server.app import create_app
from tests.helpers import new_service


class GameCycleTests(unittest.TestCase):
    # Loading a phase-one save randomizes the order once and starts the auction.
    def test_startup_determines_order_and_enters_phase_two(self):
        state = load_game_state()
        original_players = sorted(state.player_turn_order)

        self.assertEqual(state.phase, 1)
        self.assertEqual(state.current_action, DETERMINING_PLAYER_ORDER)

        new_service(state, rng=random.Random(7))

        self.assertEqual(state.phase, 2)
        self.assertEqual(state.current_action, POWER_PLANT_AUCTION)
        self.assertEqual(state.current_player, state.player_turn_order[0])
        self.assertEqual(sorted(state.player_turn_order), original_players)
        self.assertEqual(state.cycles, 0)

    # The first auction ends by ordering the resource phase by highest plant.
    def test_cycle_zero_auction_handoff_orders_by_highest_plant(self):
        state = load_game_state()
        p1, p2, p3, p4 = state.player_turn_order
        state.cycles = 0
        state.current_action = POWER_PLANT_AUCTION
        state.current_player = p1
        state.player_power_plants = {
            p1: [{"plant_id": 22}],
            p2: [{"plant_id": 33}],
            p3: [{"plant_id": 10}],
            p4: [],
        }
        service = new_service(state)

        for _ in state.player_turn_order:
            self.assertEqual(service.pass_bid(state.current_player), ErrorCode.E_OK)

        self.assertEqual(state.player_turn_order, [p2, p1, p3, p4])
        self.assertEqual(state.phase, 3)
        self.assertEqual(state.current_action, BUYING_RESOURCES)
        self.assertEqual(state.current_player, p2)

    # Every later cycle orders by houses, then highest plant, keeping the order of exact ties.
    def test_cycles_after_first_order_by_houses_then_highest_plant(self):
        state = load_game_state()
        p1, p2, p3, p4 = state.player_turn_order
        state.cycles = 1
        state.current_action = DETERMINING_PLAYER_ORDER
        state.player_power_plants = {
            p1: [{"plant_id": 15}],
            p2: [{"plant_id": 21}],
            p3: [{"plant_id": 5}],
            p4: [{"plant_id": 50}],
        }

        for spots in state.map_houses.values():
            for spot in spots:
                spots[spot] = None

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

    # Phases one to five complete in order before the cycle counter goes up.
    def test_complete_five_phase_cycle_increments_counter_and_resets_order(self):
        state = load_game_state()
        service = new_service(state, rng=random.Random(11))

        self.assertEqual(state.phase, 2)
        self.assertEqual(state.current_action, POWER_PLANT_AUCTION)
        self.assertEqual(state.cycles, 0)

        for _ in state.player_turn_order:
            self.assertEqual(service.pass_bid(state.current_player), ErrorCode.E_OK)

        self.assertEqual(state.phase, 3)
        self.assertEqual(state.current_action, BUYING_RESOURCES)

        for _ in state.player_turn_order:
            self.assertEqual(service.buy_resources(state.current_player, {}), ErrorCode.E_OK)

        self.assertEqual(state.phase, 4)
        self.assertEqual(state.current_action, BUILDING_HOUSES)
        self.assertEqual(state.current_player, state.player_turn_order[0])

        for _ in state.player_turn_order:
            self.assertEqual(service.buy_houses(state.current_player), ErrorCode.E_OK)

        self.assertEqual(state.phase, 5)
        self.assertEqual(state.current_action, BUREAUCRACY)
        self.assertEqual(state.current_player, state.player_turn_order[0])

        for _ in state.player_turn_order:
            self.assertEqual(service.bureaucracy(state.current_player), ErrorCode.E_OK)

        self.assertEqual(state.cycles, 1)
        self.assertEqual(state.phase, 2)
        self.assertEqual(state.current_action, POWER_PLANT_AUCTION)
        self.assertEqual(state.current_player, state.player_turn_order[0])
        self.assertFalse(state.phase_finished_players)

    # The header view shows the cycle counter.
    def test_cycle_count_is_in_header_view(self):
        state = load_game_state()
        state.cycles = 3
        client = create_app(new_service(state)).test_client()

        header = client.get("/api/view").get_json()["header"]

        self.assertEqual(header["cycles"], 3)

    # Every action name the game uses has a label in the header.
    def test_header_has_a_label_for_every_action(self):
        state = load_game_state()
        client = create_app(new_service(state)).test_client()
        actions = [
            DETERMINING_PLAYER_ORDER, POWER_PLANT_AUCTION, "power_plant_bidding",
            "discard_power_plant", BUYING_RESOURCES, BUILDING_HOUSES, BUREAUCRACY,
        ]

        for action in actions:
            state.current_action = action
            status = client.get("/api/view").get_json()["header"]["placement_status"]

            self.assertNotIn("_", status, action)


if __name__ == "__main__":
    unittest.main()
