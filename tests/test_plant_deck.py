import random
import unittest

from backend.data.files import load_plant_deck
from backend.game_setup.power_plant_deck import create_initial_power_plant_setup
from tests.helpers import new_auction_state, new_client


class PlantDeckTests(unittest.TestCase):
    def setUp(self):
        self.state = new_auction_state()
        self.client = new_client(self.state)
        self.plants = load_plant_deck()

    # Setup starts with eight sorted plug cards and keeps every other card in order.
    def test_initial_deck_setup(self):
        market, draw_pile = create_initial_power_plant_setup(self.plants, rng=random.Random(12))
        all_ids = set(self.plants)

        self.assertEqual(len(market), 8)
        self.assertEqual(market, sorted(market))
        self.assertTrue(all(self.plants[plant_id]["back_of_the_card"] == "plug" for plant_id in market))
        self.assertEqual(self.plants[draw_pile[0]]["back_of_the_card"], "plug")
        self.assertEqual(len(market + draw_pile), len(all_ids))
        self.assertEqual(set(market + draw_pile), all_ids)

    # The next-card indicator follows the top of the draw pile.
    def test_next_card_back_comes_from_deck_top(self):
        non_plug = None

        for plant_id, plant in self.plants.items():
            if plant["back_of_the_card"] == "no_plug":
                non_plug = plant_id
                break

        self.state.power_plant_deck[0] = non_plug

        view = self.client.get("/api/view").get_json()

        self.assertEqual(view["next_card_back"]["label"], "No Plug")

    # Buying a plant draws the next card into the market and moves the top of the pile.
    def test_award_refills_market_from_deck(self):
        p1, p2, p3, p4 = self.state.player_turn_order
        purchased_plant = self.state.power_plant_market[0]
        drawn_plant = self.state.power_plant_deck[0]
        next_deck_plant = self.state.power_plant_deck[1]

        self.client.post("/api/plant/select", json={"plant_id": purchased_plant})
        self.client.post("/api/bid", json={"player": p2, "amount": purchased_plant + 1})

        for player in (p3, p4, p1):
            self.client.post("/api/bid/pass", json={"player": player})

        self.assertNotIn(purchased_plant, self.state.power_plant_market)
        self.assertIn(drawn_plant, self.state.power_plant_market)
        self.assertEqual(self.state.power_plant_market, sorted(self.state.power_plant_market))
        self.assertEqual(self.state.power_plant_deck[0], next_deck_plant)


if __name__ == "__main__":
    unittest.main()
