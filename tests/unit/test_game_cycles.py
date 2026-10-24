import random
import unittest

from backend.data.game_state_store import load_game_state
from backend.game_setup.new_game import create_new_game_state
from backend.rules.common.constants import (
    BUILDING_HOUSES,
    BUREAUCRACY,
    BUYING_RESOURCES,
    DETERMINING_PLAYER_ORDER,
    POWER_PLANT_AUCTION,
)
from backend.rules.common.error_codes import ErrorCode
from backend.rules.common.phase_flow import start_phase_five
from backend.rules.phase_one_turn_order.initial_order import determine_initial_order
from backend.rules.phase_two_auction.auction import finish_auction
from backend.server.app import create_app
from tests.unit.helpers import new_service
from backend.views.game_view import build_view


class GameCycleTests(unittest.TestCase):
    def test_bureaucracy_replenishes_resources_and_buries_highest_plant_in_steps_one_and_two(self):
        cases = (
            (1, {"coal": 24, "oil": 12, "trash": 24, "uranium": 1}, True),
            (2, {"coal": 24, "oil": 13, "trash": 24, "uranium": 1}, True),
            (3, {"coal": 23, "oil": 14, "trash": 24, "uranium": 1}, False),
        )

        for step, expected_resources, should_bury_plant in cases:
            with self.subTest(step=step):
                state = create_new_game_state(2, rng=random.Random(step))
                state.step = step
                state.phase = 5
                state.current_action = BUREAUCRACY
                state.power_plant_market = [3, 7, 12]
                state.power_plant_deck = [25, "Step 3", 30]
                state.resource_market = {"coal": 20, "oil": 10, "trash": 23, "uranium": 0}
                service = new_service(state)

                for player in state.player_turn_order:
                    self.assertEqual(service.bureaucracy(player), ErrorCode.E_OK)

                self.assertEqual(state.resource_market, expected_resources)

                if should_bury_plant:
                    self.assertEqual(state.power_plant_market, [3, 7])
                    self.assertEqual(state.power_plant_deck, [25, "Step 3", 30, 12])
                else:
                    self.assertEqual(state.power_plant_market, [3, 7, 12])
                    self.assertEqual(state.power_plant_deck, [25, "Step 3", 30])

    def test_step_two_is_applied_at_bureaucracy_after_seventh_house(self):
        for house_count, expected_step in ((6, 1), (7, 2)):
            with self.subTest(house_count=house_count):
                state = load_game_state()
                player = state.player_turn_order[0]

                for spots in state.map_houses.values():
                    for spot in spots:
                        spots[spot] = None

                available_spots = [
                    (city, spot)
                    for city, spots in state.map_houses.items()
                    for spot in spots
                ]

                for city, spot in available_spots[:house_count]:
                    state.map_houses[city][spot] = player

                state.step = 1
                start_phase_five(state)

                self.assertEqual(state.phase, 5)
                self.assertEqual(state.step, expected_step)

    # New-game setup explicitly determines order; loading a saved state does not do this.
    def test_new_game_determines_order_and_enters_phase_two(self):
        rng = random.Random(7)
        state = create_new_game_state(4, rng=rng)
        original_players = sorted(state.player_turn_order)

        self.assertEqual(state.phase, 1)
        self.assertEqual(state.current_action, DETERMINING_PLAYER_ORDER)

        self.assertEqual(determine_initial_order(state, rng), ErrorCode.E_OK)

        self.assertEqual(state.phase, 2)
        self.assertEqual(state.current_action, POWER_PLANT_AUCTION)
        self.assertEqual(state.current_player, state.player_turn_order[0])
        self.assertEqual(sorted(state.player_turn_order), original_players)
        self.assertEqual(state.cycles, 0)

    # Resource buying proceeds opposite the auction's highest-plant order.
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
        state.players_bought_power_plant = list(state.player_turn_order)
        finish_auction(state)

        self.assertEqual(state.player_turn_order, [p2, p1, p3, p4])
        self.assertEqual(state.phase, 3)
        self.assertEqual(state.current_action, BUYING_RESOURCES)
        self.assertEqual(state.current_player, state.player_turn_order[-1])

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
        rng = random.Random(11)
        state = create_new_game_state(4, rng=rng)
        self.assertEqual(determine_initial_order(state, rng), ErrorCode.E_OK)
        state.cycles = 1
        service = new_service(state, rng=rng)

        self.assertEqual(state.phase, 2)
        self.assertEqual(state.current_action, POWER_PLANT_AUCTION)
        self.assertEqual(state.cycles, 1)

        for _ in state.player_turn_order:
            self.assertEqual(service.pass_bid(state.current_player), ErrorCode.E_OK)

        self.assertEqual(state.phase, 3)
        self.assertEqual(state.current_action, BUYING_RESOURCES)

        for _ in state.player_turn_order:
            self.assertEqual(service.buy_resources(state.current_player, {}), ErrorCode.E_OK)

        self.assertEqual(state.phase, 4)
        self.assertEqual(state.current_action, BUILDING_HOUSES)
        self.assertEqual(state.current_player, state.player_turn_order[-1])
        house_order = []

        for _ in state.player_turn_order:
            house_order.append(state.current_player)
            self.assertEqual(service.buy_houses(state.current_player), ErrorCode.E_OK)

        self.assertEqual(house_order, list(reversed(state.player_turn_order)))

        self.assertEqual(state.phase, 5)
        self.assertEqual(state.current_action, BUREAUCRACY)
        waiting_view = build_view(state)
        self.assertFalse(waiting_view["header"]["show_turn_order"])
        self.assertFalse(waiting_view["header"]["turn_order"])
        self.assertIn("Waiting for all players", waiting_view["header"]["placement_status"])
        self.assertTrue(all(player["can_power"] for player in waiting_view["players"]))

        first_power_player = state.player_turn_order[1]
        self.assertEqual(service.bureaucracy(first_power_player), ErrorCode.E_OK)
        self.assertEqual(service.bureaucracy(first_power_player), ErrorCode.E_NOT_OKAY)
        after_first_power = build_view(state)
        power_buttons = {player["player"]: player["can_power"] for player in after_first_power["players"]}
        self.assertFalse(power_buttons[first_power_player])
        self.assertTrue(all(power_buttons[player] for player in state.player_turn_order if player != first_power_player))

        for player in state.player_turn_order:
            if player != first_power_player:
                self.assertEqual(service.bureaucracy(player), ErrorCode.E_OK)

        self.assertEqual(state.cycles, 2)
        self.assertEqual(state.phase, 2)
        self.assertEqual(state.current_action, POWER_PLANT_AUCTION)
        self.assertEqual(state.current_player, state.player_turn_order[0])
        self.assertFalse(state.phase_finished_players)

    def test_step_two_starts_when_bureaucracy_begins_after_seventh_house(self):
        rng = random.Random(13)
        state = create_new_game_state(2, rng=rng)
        determine_initial_order(state, rng)
        state.phase = 4
        state.current_action = BUILDING_HOUSES
        state.step = 1
        player = state.player_turn_order[0]
        city_spots = [
            (city, spot)
            for city, spots in state.map_houses.items()
            for spot in spots
        ][:7]

        for city, spot in city_spots:
            state.map_houses[city][spot] = player

        state.current_player = state.player_turn_order[-1]
        service = new_service(state)

        for player_in_turn in reversed(state.player_turn_order):
            self.assertEqual(service.buy_houses(player_in_turn), ErrorCode.E_OK)

        self.assertEqual(state.current_action, BUREAUCRACY)
        self.assertEqual(state.step, 2)

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
