import random
import unittest

from backend.data.files import load_plant_deck, load_plant_removal
from backend.game_setup.power_plant_deck import (
    create_initial_power_plant_setup,
    prepare_initial_power_plant_deck,
)
from tests.helpers import new_auction_state, new_client


class PlantDeckTests(unittest.TestCase):
    def setUp(self):
        self.state = new_auction_state()
        self.client = new_client(self.state)
        self.plants = load_plant_deck()

    # Setup starts with eight sorted plug cards and keeps every other card in order.
    def test_initial_deck_setup(self):
        market, draw_pile, removed = create_initial_power_plant_setup(
            self.plants, 4, rng=random.Random(12),
        )
        all_ids = set(self.plants)

        self.assertEqual(len(market), 8)
        self.assertEqual(market, sorted(market))
        self.assertTrue(all(self.plants[plant_id]["back_of_the_card"] == "plug" for plant_id in market))
        self.assertEqual(self.plants[draw_pile[0]]["back_of_the_card"], "plug")
        self.assertEqual(len(removed), 4)
        self.assertEqual(set(market + draw_pile + removed), all_ids)
        self.assertEqual(len(market + draw_pile + removed), len(all_ids))

    def test_removal_counts_follow_player_count(self):
        settings = load_plant_removal()

        for number_of_players in range(2, 7):
            with self.subTest(number_of_players=number_of_players):
                market, draw_pile, removed = create_initial_power_plant_setup(
                    self.plants,
                    number_of_players,
                    rng=random.Random(number_of_players),
                )
                expected = settings[f"{number_of_players}_players"]
                actual = {
                    "plug": sum(self.plants[plant_id]["back_of_the_card"] == "plug" for plant_id in removed),
                    "no_plug": sum(self.plants[plant_id]["back_of_the_card"] == "no_plug" for plant_id in removed),
                }

                self.assertEqual(actual, expected)
                self.assertFalse(set(removed) & set(market + draw_pile))
                self.assertEqual(set(market + draw_pile + removed), set(self.plants))

    def test_prepared_deck_and_removed_plants_are_stored_in_game_state(self):
        prepare_initial_power_plant_deck(self.state, self.plants, rng=random.Random(12))

        self.assertEqual(len(self.state.removed_power_plants), 4)
        self.assertEqual(
            set(self.state.power_plant_market + self.state.power_plant_deck + self.state.removed_power_plants),
            set(self.plants),
        )

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
