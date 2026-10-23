import random
import unittest
from copy import deepcopy

from backend.application.game_service import GameService
from backend.data.files import load_plant_deck
from backend.game_setup.power_plant_deck import create_initial_power_plant_setup
from backend.server.main import app


class PlantDeckTests(unittest.TestCase):
    def setUp(self):
        self.original_service = app.config["game_service"]
        self.state = deepcopy(self.original_service.snapshot())
        app.config["game_service"] = GameService(self.state, lambda state: None)
        self.client = app.test_client()
        self.plants = load_plant_deck()

    def tearDown(self):
        app.config["game_service"] = self.original_service

    # Setup starts with eight sorted plug cards and keeps every other card in order.
    def test_initial_deck_setup(self):
        market, draw_pile = create_initial_power_plant_setup(
            self.plants,
            rng=random.Random(12),
        )
        all_ids = set(self.plants)

        self.assertEqual(len(market), 8)
        self.assertEqual(market, sorted(market))
        self.assertTrue(all(self.plants[plant_id]["back_of_the_card"] == "plug" for plant_id in market))
        self.assertEqual(self.plants[draw_pile[0]]["back_of_the_card"], "plug")
        self.assertEqual(len(market + draw_pile), len(all_ids))
        self.assertEqual(set(market + draw_pile), all_ids)
        self.assertTrue(all(not player_plants for player_plants in self.state.player_power_plants.values()))

    # The next-card indicator follows the draw-pile head, not a duplicate state field.
    def test_next_card_back_comes_from_deck_top(self):
        non_plug = next(
            plant_id
            for plant_id, plant in self.plants.items()
            if plant["back_of_the_card"] == "no_plug"
        )
        self.state.power_plant_deck[0] = non_plug

        view = self.client.get("/api/view").get_json()

        self.assertEqual(view["next_card_back"]["label"], "No Plug")

    # Buying a plant draws the next card into the market and advances the deck head.
    def test_award_refills_market_from_deck(self):
        self.state.current_action = "power_plant_auction"
        p1, p2, p3, p4 = self.state.player_turn_order
        self.state.current_player = p1
        purchased_plant = self.state.power_plant_market[0]
        drawn_plant = self.state.power_plant_deck[0]
        next_deck_plant = self.state.power_plant_deck[1]

        self.assertEqual(
            self.client.post("/api/plant/select", json={"plant_id": purchased_plant}).status_code,
            200,
        )
        self.assertEqual(
            self.client.post("/api/bid", json={"player": p2, "amount": purchased_plant + 1}).status_code,
            200,
        )
        for player in (p3, p4, p1):
            self.assertEqual(
                self.client.post("/api/bid/pass", json={"player": player}).status_code,
                200,
            )

        self.assertNotIn(purchased_plant, self.state.power_plant_market)
        self.assertIn(drawn_plant, self.state.power_plant_market)
        self.assertEqual(self.state.power_plant_market, sorted(self.state.power_plant_market))
        self.assertEqual(self.state.power_plant_deck[0], next_deck_plant)


if __name__ == "__main__":
    unittest.main()