import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.application.game_service import GameService
from backend.data.files import load_settings
from backend.data import game_state_store
from backend.data.game_state_store import list_saved_games, load_game_state, save_game_state
from backend.game_setup.new_game import create_new_game_state
from backend.rules.common.error_codes import ErrorCode
from backend.rules.common.constants import DETERMINING_PLAYER_ORDER, POWER_PLANT_AUCTION
from backend.server.app import create_app
from backend.game_setup.starting_money import STARTING_MONEY, create_initial_player_money


class GameSetupTests(unittest.TestCase):
    def test_starting_money_is_created_for_every_player_and_matches_save(self):
        players = ["p1", "p2", "p3", "p4"]
        expected = {player: STARTING_MONEY for player in players}

        self.assertEqual(STARTING_MONEY, 50)
        self.assertEqual(create_initial_player_money(players), expected)

    def test_new_game_uses_player_count_and_never_loads_save(self):
        saves = []
        app = create_app(
            load_state=lambda: self.fail("New Game must not load a saved game"),
            save_state=lambda state: saves.append(state.to_dict()),
            plant_slots_per_player=load_settings()["rules"]["plant_slots_per_player"],
        )
        client = app.test_client()

        self.assertEqual(client.get("/api/view").status_code, 400)
        self.assertEqual(client.post("/api/new-game", json={"number_of_players": 1}).status_code, 400)
        self.assertEqual(client.post("/api/new-game", json={"number_of_players": 7}).status_code, 400)
        self.assertEqual(client.post("/api/new-game", json={"number_of_players": 2}).status_code, 200)

        self.assertEqual(len(saves), 1)
        self.assertTrue(saves[0]["game_started"])
        self.assertEqual(saves[0]["number_of_players"], 2)
        self.assertEqual(saves[0]["current_action"], POWER_PLANT_AUCTION)
        self.assertEqual(len(saves[0]["player_turn_order"]), 2)
        self.assertEqual(len(saves[0]["regions_chosen"]), 3)
        self.assertTrue(all(money == STARTING_MONEY for money in saves[0]["player_money"].values()))
        self.assertTrue(all(not owner for spots in saves[0]["map_houses"].values() for owner in spots.values()))
        self.assertTrue(all(not plants for plants in saves[0]["player_power_plants"].values()))
        self.assertEqual(saves[0]["resource_market"], {"coal": 24, "oil": 18, "trash": 9, "uranium": 2})

        self.assertEqual(client.post("/api/save-game").status_code, 200)
        self.assertEqual(len(saves), 2)
        self.assertEqual(client.post("/api/new-game", json={"number_of_players": 3}).status_code, 400)

    def test_load_game_preserves_saved_areas_and_player_order(self):
        save_id = list_saved_games()[0]["id"]
        state = load_game_state(save_id)
        state.current_action = DETERMINING_PLAYER_ORDER
        state.phase = 1
        state.player_turn_order.reverse()
        expected_order = list(state.player_turn_order)
        expected_regions = list(state.regions_chosen)
        loaded = []
        app = create_app(
            load_state=lambda selected_id: loaded.append(selected_id) or state,
            save_state=lambda saved: None,
            plant_slots_per_player=load_settings()["rules"]["plant_slots_per_player"],
        )
        client = app.test_client()

        self.assertEqual(client.post("/api/load-game", json={"save_id": save_id}).status_code, 200)
        self.assertEqual(loaded, [save_id])
        restored = app.config["game_service"].snapshot()
        self.assertEqual(restored.current_action, DETERMINING_PLAYER_ORDER)
        self.assertEqual(restored.player_turn_order, expected_order)
        self.assertEqual(restored.regions_chosen, expected_regions)
        self.assertEqual(client.get("/ui/start.html").status_code, 302)

    def test_timestamped_saves_are_listed_and_loaded_independently(self):
        state = create_new_game_state(2, rng=random.Random(3))
        first_order = list(state.player_turn_order)

        with tempfile.TemporaryDirectory() as temporary_directory:
            with patch.object(game_state_store, "GAME_SAVE_DIR", Path(temporary_directory)):
                first_id = save_game_state(state)
                state.player_turn_order.reverse()
                second_order = list(state.player_turn_order)
                second_id = save_game_state(state)
                saves = list_saved_games()

                self.assertNotEqual(first_id, second_id)
                self.assertEqual([save["id"] for save in saves], [second_id, first_id])
                self.assertTrue(all("saved_at" in save and "number_of_players" in save for save in saves))
                self.assertEqual(load_game_state(first_id).player_turn_order, first_order)
                self.assertEqual(load_game_state(second_id).player_turn_order, second_order)

    def test_new_game_factory_rejects_invalid_player_counts(self):
        for player_count in (1, 7, True, 2.5):
            with self.subTest(player_count=player_count):
                with self.assertRaises(ValueError):
                    create_new_game_state(player_count, rng=random.Random(9))


if __name__ == "__main__":
    unittest.main()