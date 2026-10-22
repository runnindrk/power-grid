import unittest
from copy import deepcopy

from backend.application.game_service import GameService
from backend.server.main import app


class AuctionWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.original_service = app.config["game_service"]
        # Each test gets an isolated copy and cannot alter the real save-game state.
        self.state = deepcopy(self.original_service.snapshot())
        self.state.current_action = "power_plant_auction"
        self.state.current_player = self.state.player_turn_order[0]
        app.config["game_service"] = GameService(self.state, lambda state: None)
        self.client = app.test_client()

    def tearDown(self):
        app.config["game_service"] = self.original_service

    # A different winner leaves the selector active; the buyer sits out later auctions.
    def test_selector_continues_after_another_player_wins(self):
        p1, p2, p3, p4 = self.state.player_turn_order
        self.state.current_player = p2
        plant_id = self.state.power_plant_market[0]
        second_plant_id = self.state.power_plant_market[1]
        starting_money = self.state.player_money[p3]

        response = self.client.post("/api/plant/select", json={"plant_id": plant_id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.state.auction_bids, {p2: plant_id})
        self.assertEqual(self.state.current_player, p3)

        response = self.client.post("/api/bid", json={"player": p3, "amount": plant_id + 4})
        self.assertEqual(response.status_code, 200)

        for player in (p4, p1, p2):
            response = self.client.post("/api/bid/pass", json={"player": player})
            self.assertEqual(response.status_code, 200)

        self.assertEqual(self.state.player_money[p3], starting_money - plant_id - 4)
        self.assertIn(
            plant_id,
            [plant["plant_id"] for plant in self.state.player_power_plants[p3]],
        )
        self.assertNotIn(plant_id, self.state.power_plant_market)
        self.assertEqual(self.state.current_action, "power_plant_auction")
        self.assertEqual(self.state.current_player, p2)

        response = self.client.post("/api/plant/select", json={"plant_id": second_plant_id})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(p3, self.state.auction_participants)

    # A winner with full plant slots must discard one before the auction resumes.
    def test_full_plant_slots_require_discard(self):
        p1, p2, p3, p4 = self.state.player_turn_order
        existing_plant_ids = [31, 46, 50]
        self.state.power_plant_deck = [
            plant_id
            for plant_id in self.state.power_plant_deck
            if plant_id not in existing_plant_ids
        ]
        self.state.player_power_plants[p2] = [
            {
                "plant_id": plant_id,
                "resources": {
                    "coal": 0,
                    "oil": 0,
                    "trash": 0,
                    "gas": 0,
                    "uranium": 0,
                },
                "ready_to_power": False,
            }
            for plant_id in existing_plant_ids
        ]
        plant_id = self.state.power_plant_market[0]
        discarded_plant_id = self.state.player_power_plants[p2][0]["plant_id"]

        self.assertEqual(
            self.client.post("/api/plant/select", json={"plant_id": plant_id}).status_code,
            200,
        )
        self.assertEqual(
            self.client.post("/api/bid", json={"player": p2, "amount": plant_id + 1}).status_code,
            200,
        )
        for player in (p3, p4, p1):
            self.assertEqual(
                self.client.post("/api/bid/pass", json={"player": player}).status_code,
                200,
            )

        self.assertEqual(self.state.current_action, "discard_power_plant")
        self.assertEqual(self.state.pending_plant_replacement["plant_id"], plant_id)
        self.assertEqual(len(self.state.player_power_plants[p2]), 3)

        view = self.client.get("/api/view").get_json()
        pending_header = view["header"]["turn_order"]
        p2_turn = next(player for player in pending_header if player["label"] == self.state.player_aliases[p2])
        self.assertNotIn("finished", p2_turn["classes"])

        p2_view = next(player for player in view["players"] if player["player"] == p2)
        p1_view = next(player for player in view["players"] if player["player"] == p1)
        self.assertTrue(all(plant["discardable"] for plant in p2_view["plant_slots"]))
        self.assertFalse(any(plant.get("discardable") for plant in p1_view["plant_slots"]))

        invalid = self.client.post(
            "/api/plant/discard",
            json={"player": p2, "plant_id": plant_id},
        )
        self.assertEqual(invalid.status_code, 400)

        response = self.client.post(
            "/api/plant/discard",
            json={"player": p2, "plant_id": discarded_plant_id},
        )
        self.assertEqual(response.status_code, 200)
        owned_ids = [plant["plant_id"] for plant in self.state.player_power_plants[p2]]
        self.assertNotIn(discarded_plant_id, owned_ids)
        self.assertIn(plant_id, owned_ids)
        self.assertEqual(len(owned_ids), 3)
        self.assertEqual(self.state.current_action, "power_plant_auction")
        self.assertEqual(self.state.current_player, p1)

        finished_header = self.client.get("/api/view").get_json()["header"]["turn_order"]
        p2_turn = next(player for player in finished_header if player["label"] == self.state.player_aliases[p2])
        self.assertIn("finished", p2_turn["classes"])

        for player in (p1, p3, p4):
            self.assertEqual(
                self.client.post("/api/bid/pass", json={"player": player}).status_code,
                200,
            )

        self.assertEqual(self.state.current_action, "building_houses")
        next_phase_header = self.client.get("/api/view").get_json()["header"]["turn_order"]
        self.assertTrue(all("finished" not in player["classes"] for player in next_phase_header))

    # Passing on selection through the whole turn order advances to house-building.
    def test_all_selectors_pass(self):
        for player in self.state.player_turn_order:
            response = self.client.post("/api/bid/pass", json={"player": player})
            self.assertEqual(response.status_code, 200)

        self.assertEqual(self.state.current_action, "building_houses")
        self.assertIsNone(self.state.selected_power_plant)
        self.assertFalse(self.state.players_bought_power_plant)

    # A stale player cannot invoke a turn-ending board action.
    def test_stale_player_cannot_end_turn(self):
        current_player = self.state.current_player
        stale_player = self.state.player_turn_order[-1]
        response = self.client.post("/api/buy-houses", json={"player": stale_player})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.state.current_player, current_player)

    # Resource and house actions record completion under separate phase keys.
    def test_completion_markers_are_scoped_to_phase(self):
        p1, p2, _, _ = self.state.player_turn_order
        self.state.current_action = "buying_resources"

        response = self.client.post(
            "/api/buy-resources",
            json={"player": p1, "resources": {}},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.state.phase_finished_players["phase_three_resource_buying"],
            [p1],
        )

        self.state.current_action = "building_houses"
        self.state.current_player = p2
        response = self.client.post("/api/buy-houses", json={"player": p2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.state.phase_finished_players["phase_four_building_houses"],
            [p2],
        )

        header = self.client.get("/api/view").get_json()["header"]["turn_order"]
        p1_view = next(player for player in header if player["label"] == self.state.player_aliases[p1])
        p2_view = next(player for player in header if player["label"] == self.state.player_aliases[p2])
        self.assertNotIn("finished", p1_view["classes"])
        self.assertIn("finished", p2_view["classes"])


if __name__ == "__main__":
    unittest.main()