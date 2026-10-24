import random
import unittest

from backend.application.game_service import GameService
from backend.data.files import load_money
from backend.game_setup.new_game import create_new_game_state
from backend.rules.common.constants import BUREAUCRACY
from backend.rules.common.error_codes import ErrorCode
from backend.rules.common.player_plants import can_power_plant, new_power_plant
from backend.rules.phase_five_bureaucracy.bureaucracy import bureaucracy
from backend.views.game_view import build_view


class BureaucracyTests(unittest.TestCase):
    def setUp(self):
        self.state = create_new_game_state(2, rng=random.Random(23))
        self.player = self.state.player_turn_order[0]
        self.state.player_money[self.player] = 0
        self.state.player_power_plants[self.player] = []
        self.income_table = load_money()["money"][0]
        self.plants = {
            4: {"coal": 2, "oil": 0, "trash": 0, "gas": 0, "uranium": 0, "houses": 1, "hybrid": False},
            5: {"coal": 2, "oil": 2, "trash": 0, "gas": 0, "uranium": 0, "houses": 2, "hybrid": True},
            7: {"coal": 0, "oil": 3, "trash": 0, "gas": 0, "uranium": 0, "houses": 2, "hybrid": False},
            13: {"coal": 0, "oil": 0, "trash": 0, "gas": 0, "uranium": 0, "houses": 1, "hybrid": False},
        }

        for spots in self.state.map_houses.values():
            for spot in spots:
                spots[spot] = None

    def set_houses(self, count):
        for city, spots in self.state.map_houses.items():
            if count == 0:
                return
            spots["spot_1"] = self.player
            count -= 1

    def test_ready_plants_burn_fuel_and_power_only_owned_houses(self):
        self.set_houses(2)
        coal_plant = new_power_plant(4)
        coal_plant["resources"]["coal"] = 2
        coal_plant["ready_to_power"] = True
        oil_plant = new_power_plant(7)
        oil_plant["resources"]["oil"] = 3
        oil_plant["ready_to_power"] = True
        self.state.player_power_plants[self.player] = [coal_plant, oil_plant]

        result = bureaucracy(self.state, self.player, self.plants, self.income_table)

        self.assertEqual(result, ErrorCode.E_OK)
        self.assertEqual(self.state.player_money[self.player], 33)
        self.assertEqual(coal_plant["resources"]["coal"], 0)
        self.assertEqual(oil_plant["resources"]["oil"], 0)
        self.assertFalse(coal_plant["ready_to_power"])
        self.assertFalse(oil_plant["ready_to_power"])

    def test_underfueled_ready_plant_does_not_burn_or_power(self):
        self.set_houses(4)
        plant = new_power_plant(4)
        plant["resources"]["coal"] = 1
        plant["ready_to_power"] = True
        self.state.player_power_plants[self.player] = [plant]

        result = bureaucracy(self.state, self.player, self.plants, self.income_table)

        self.assertEqual(result, ErrorCode.E_OK)
        self.assertEqual(self.state.player_money[self.player], 10)
        self.assertEqual(plant["resources"]["coal"], 1)
        self.assertFalse(plant["ready_to_power"])

    def test_hybrid_plant_can_burn_a_mix_of_its_fuels(self):
        self.set_houses(2)
        plant = new_power_plant(5)
        plant["resources"] = {"oil": 2, "coal": 1, "trash": 0, "gas": 0, "uranium": 0}
        plant["ready_to_power"] = True
        self.state.player_power_plants[self.player] = [plant]

        result = bureaucracy(self.state, self.player, self.plants, self.income_table)

        self.assertEqual(result, ErrorCode.E_OK)
        self.assertEqual(self.state.player_money[self.player], 33)
        self.assertEqual(plant["resources"]["oil"], 0)
        self.assertEqual(plant["resources"]["coal"], 1)

    def test_ready_toggle_is_blocked_until_plant_has_enough_fuel(self):
        plant = new_power_plant(4)
        plant["resources"]["coal"] = 1
        self.state.player_power_plants[self.player] = [plant]
        service = GameService(self.state, lambda saved: None)

        self.assertFalse(can_power_plant(plant, self.plants[4]))
        self.assertEqual(service.toggle_ready_to_power(self.player, 4), ErrorCode.E_NOT_OKAY)
        self.assertTrue(next(
            card["ready_to_power"] for player_view in build_view(self.state)["players"]
            if player_view["player"] == self.player
            for card in player_view["plant_slots"] if card.get("plant_id") == 4
        )["disabled"])

        plant["resources"]["coal"] = 2
        self.assertTrue(can_power_plant(plant, self.plants[4]))
        self.assertEqual(service.toggle_ready_to_power(self.player, 4), ErrorCode.E_OK)
        self.assertTrue(plant["ready_to_power"])

    def test_ready_plant_turns_off_when_resource_move_leaves_it_underfueled(self):
        plant = new_power_plant(4)
        plant["resources"]["coal"] = 2
        plant["ready_to_power"] = True
        target = new_power_plant(10)
        self.state.player_power_plants[self.player] = [plant, target]
        service = GameService(self.state, lambda saved: None)

        self.assertEqual(service.transfer_resource(self.player, 4, 0, 10, 0), ErrorCode.E_OK)
        self.assertFalse(plant["ready_to_power"])
        self.assertEqual(plant["resources"]["coal"], 1)
        self.assertEqual(target["resources"]["coal"], 1)

    def test_resource_free_ready_plant_powers_normally(self):
        self.set_houses(1)
        plant = new_power_plant(13)
        plant["ready_to_power"] = True
        self.state.player_power_plants[self.player] = [plant]

        result = bureaucracy(self.state, self.player, self.plants, self.income_table)

        self.assertEqual(result, ErrorCode.E_OK)
        self.assertEqual(self.state.player_money[self.player], 22)
        self.assertFalse(plant["ready_to_power"])

    def test_game_service_power_action_pays_and_marks_player_finished(self):
        self.set_houses(1)
        self.state.phase = 5
        self.state.current_action = BUREAUCRACY
        self.state.current_player = self.player
        plant = new_power_plant(13)
        plant["ready_to_power"] = True
        self.state.player_power_plants[self.player] = [plant]
        service = GameService(self.state, lambda saved: None)

        result = service.bureaucracy(self.player)

        self.assertEqual(result, ErrorCode.E_OK)
        self.assertEqual(self.state.player_money[self.player], 22)
        self.assertIn(self.player, self.state.phase_finished_players["phase_five_bureaucracy"])


if __name__ == "__main__":
    unittest.main()
