import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.data import game_state_store
from backend.data.files import load_plant_deck, load_plant_removal
from backend.game_setup.power_plant_deck import (
    create_initial_power_plant_setup,
    prepare_initial_power_plant_deck,
)
from backend.rules.phase_two_auction.auction import award_power_plant
from tests.unit.helpers import new_auction_state, new_client


class PlantDeckTests(unittest.TestCase):
    def setUp(self):
        self.state = new_auction_state()
        self.client = new_client(self.state)
        self.plants = load_plant_deck()
        self.special_cards = [
            card_id for card_id, card in self.plants.items()
            if "cost" not in card
        ]
        self.step_card = next(card_id for card_id in self.special_cards if card_id.startswith("Step "))

    # Setup starts with eight sorted plug cards and keeps every other card in order.
    def test_initial_deck_setup(self):
        market, draw_pile, removed = create_initial_power_plant_setup(
            self.plants, 4, rng=random.Random(12),
        )
        physical_ids = {card_id for card_id, card in self.plants.items() if "cost" in card}
        physical_draw_pile = draw_pile[:-len(self.special_cards)]

        self.assertEqual(len(market), 8)
        self.assertEqual(market, sorted(market))
        self.assertTrue(all(self.plants[plant_id]["back_of_the_card"] == "plug" for plant_id in market))
        self.assertEqual(self.plants[physical_draw_pile[0]]["back_of_the_card"], "plug")
        self.assertEqual(draw_pile[-1], self.step_card)
        self.assertEqual(len(removed), 4)
        self.assertEqual(set(market + physical_draw_pile + removed), physical_ids)
        self.assertEqual(len(market + physical_draw_pile + removed), len(physical_ids))
        self.assertEqual(self.step_card, "Step 3")
        self.assertEqual(self.plants[self.step_card]["back_of_the_card"], "no_plug")

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
                physical_ids = {card_id for card_id, card in self.plants.items() if "cost" in card}
                physical_draw_pile = draw_pile[:-len(self.special_cards)]
                self.assertFalse(set(removed) & set(market + draw_pile))
                self.assertEqual(draw_pile[-1], self.step_card)
                self.assertEqual(set(market + physical_draw_pile + removed), physical_ids)

    def test_prepared_deck_and_removed_plants_are_stored_in_game_state(self):
        prepare_initial_power_plant_deck(self.state, self.plants, rng=random.Random(12))

        self.assertEqual(len(self.state.removed_power_plants), 4)
        self.assertEqual(self.state.power_plant_deck[-1], self.step_card)
        self.assertEqual(
            set(self.state.power_plant_market + self.state.power_plant_deck[:-len(self.special_cards)] + self.state.removed_power_plants),
            {card_id for card_id, card in self.plants.items() if "cost" in card},
        )

    def test_loading_pre_step_three_save_appends_marker_without_shuffling(self):
        physical_deck = [card for card in self.state.power_plant_deck if card not in self.special_cards]
        self.state.power_plant_deck = list(physical_deck)
        self.state.step = 2

        with tempfile.TemporaryDirectory() as temporary_directory:
            with patch.object(game_state_store, "GAME_SAVE_DIR", Path(temporary_directory)):
                save_id = game_state_store.save_game_state(self.state)
                loaded = game_state_store.load_game_state(save_id)

                self.assertEqual(loaded.power_plant_deck, physical_deck + self.special_cards)

                loaded.step = 3
                loaded.power_plant_deck = list(physical_deck)
                step_three_save = game_state_store.save_game_state(loaded)
                loaded_step_three = game_state_store.load_game_state(step_three_save)

                self.assertEqual(loaded_step_three.power_plant_deck, physical_deck)

    def test_save_round_trip_preserves_step_three_card_position(self):
        self.state.step = 2
        self.state.power_plant_deck = [25, self.step_card, 30, 12]

        with tempfile.TemporaryDirectory() as temporary_directory:
            with patch.object(game_state_store, "GAME_SAVE_DIR", Path(temporary_directory)):
                save_id = game_state_store.save_game_state(self.state)
                loaded = game_state_store.load_game_state(save_id)

        self.assertEqual(loaded.power_plant_deck, [25, self.step_card, 30, 12])

    def test_drawing_step_three_marker_changes_step_without_adding_a_plant(self):
        starter, winner = self.state.player_turn_order[:2]
        plant_id = self.state.power_plant_market[0]
        self.state.cycles = 1
        self.state.current_action = "power_plant_bidding"
        self.state.current_player = winner
        self.state.auction_starter = starter
        self.state.selected_power_plant = plant_id
        self.state.auction_participants = [starter, winner]
        self.state.auction_bids = {starter: plant_id, winner: plant_id + 1}
        self.state.auction_passed = [starter]
        self.state.power_plant_deck = [self.step_card]

        award_power_plant(self.state, winner, 3)

        self.assertEqual(self.state.step, 3)
        self.assertNotIn(self.step_card, self.state.power_plant_market)
        self.assertEqual(len(self.state.power_plant_market), 7)
        self.assertEqual(self.state.current_action, "power_plant_auction")
        self.assertEqual(self.state.current_player, starter)

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

    def test_next_card_preview_identifies_step_three_marker(self):
        self.state.power_plant_deck = [self.step_card]

        view = self.client.get("/api/view").get_json()

        self.assertEqual(view["next_card_back"]["label"], "Step 3")
        self.assertIn("no_plug", view["next_card_back"]["classes"])

    # Buying a plant draws the next card into the market and moves the top of the pile.
    def test_award_refills_market_from_deck(self):
        self.state.cycles = 1
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
