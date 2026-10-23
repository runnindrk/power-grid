import unittest

from backend.rules.common.constants import (
    BUYING_RESOURCES,
    DISCARD_POWER_PLANT,
    POWER_PLANT_AUCTION,
    POWER_PLANT_BIDDING,
    PHASE_THREE_RESOURCE_BUYING,
    PHASE_FOUR_BUILDING_HOUSES,
)
from backend.rules.common.player_plants import new_power_plant
from tests.helpers import find_by_label, new_auction_state, new_client


class AuctionWorkflowTests(unittest.TestCase):
    def setUp(self):
        # Every test gets its own state, so the real save game is never changed.
        self.state = new_auction_state()
        self.client = new_client(self.state)

    def post(self, url, **payload):
        """Send an action to the server and return the HTTP status code."""
        return self.client.post(url, json=payload).status_code

    def header_row(self, player):
        """Return the turn order entry of a player in the header view."""
        header = self.client.get("/api/view").get_json()["header"]["turn_order"]

        return find_by_label(header, self.state.player_aliases[player])

    def test_passed_bidder_gets_black_line_without_finishing_auction_phase(self):
        starter, passed_player, _, _ = self.state.player_turn_order
        plant_id = self.state.power_plant_market[0]
        self.state.current_action = POWER_PLANT_BIDDING
        self.state.current_player = passed_player
        self.state.auction_starter = starter
        self.state.selected_power_plant = plant_id
        self.state.auction_participants = list(self.state.player_turn_order)
        self.state.auction_bids = {starter: plant_id}

        self.assertEqual(self.post("/api/bid/pass", player=passed_player), 200)

        row = self.header_row(passed_player)
        self.assertIn("passed", row["classes"])
        self.assertNotIn("finished", row["classes"])
        self.assertIn(passed_player, self.state.auction_passed)
        self.assertNotIn(passed_player, self.state.phase_finished_players.get("phase_two_auction", []))

    def test_cycle_zero_selector_can_pass_after_others_raise_and_reselect(self):
        starter, first_bidder, winning_bidder, already_passed = self.state.player_turn_order
        plant_id = self.state.power_plant_market[0]
        self.state.current_action = POWER_PLANT_BIDDING
        self.state.current_player = starter
        self.state.auction_starter = starter
        self.state.selected_power_plant = plant_id
        self.state.auction_participants = list(self.state.player_turn_order)
        self.state.auction_bids = {
            starter: plant_id,
            first_bidder: plant_id + 1,
            winning_bidder: plant_id + 2,
        }
        self.state.auction_passed = [already_passed]

        starter_view = find_by_label(
            self.client.get("/api/view").get_json()["players"],
            self.state.player_aliases[starter],
        )
        self.assertFalse(starter_view["bid"]["pass_disabled"])
        self.assertEqual(self.post("/api/bid/pass", player=starter), 200)
        self.assertIn("passed", self.header_row(starter)["classes"])
        self.assertEqual(self.state.current_player, first_bidder)

        self.assertEqual(self.post("/api/bid/pass", player=first_bidder), 200)
        self.assertIn(winning_bidder, self.state.players_bought_power_plant)
        self.assertNotIn(starter, self.state.players_bought_power_plant)
        self.assertEqual(self.state.current_action, POWER_PLANT_AUCTION)
        self.assertEqual(self.state.current_player, starter)
        self.assertNotIn("passed", self.header_row(starter)["classes"])

        second_plant_id = self.state.power_plant_market[0]
        self.assertEqual(self.post("/api/plant/select", plant_id=second_plant_id), 200)
        self.assertNotIn(winning_bidder, self.state.auction_participants)

    def test_later_cycle_selector_can_pass_during_bidding(self):
        starter = self.state.player_turn_order[0]
        plant_id = self.state.power_plant_market[0]
        self.state.cycles = 1
        self.state.current_action = POWER_PLANT_BIDDING
        self.state.current_player = starter
        self.state.auction_starter = starter
        self.state.selected_power_plant = plant_id
        self.state.auction_participants = list(self.state.player_turn_order)
        self.state.auction_bids = {starter: plant_id}

        self.assertEqual(self.post("/api/bid/pass", player=starter), 200)
        self.assertIn(starter, self.state.auction_passed)

    def test_later_cycle_selection_out_persists_through_later_auctions(self):
        self.state.cycles = 1
        out_player, selector, next_bidder, last_bidder = self.state.player_turn_order

        self.assertEqual(self.post("/api/bid/pass", player=out_player), 200)
        self.assertIn(out_player, self.state.auction_skipped)
        self.assertIn("out", self.header_row(out_player)["classes"])
        self.assertEqual(self.state.current_player, selector)

        plant_id = self.state.power_plant_market[0]
        self.assertEqual(self.post("/api/plant/select", plant_id=plant_id), 200)
        self.assertNotIn(out_player, self.state.auction_participants)

        self.assertEqual(self.state.current_player, next_bidder)
        self.assertEqual(self.post("/api/bid/pass", player=next_bidder), 200)
        self.assertEqual(self.state.current_player, last_bidder)
        self.assertEqual(self.post("/api/bid/pass", player=last_bidder), 200)
        self.assertIn(selector, self.state.players_bought_power_plant)
        self.assertEqual(self.state.current_player, next_bidder)
        self.assertIn(out_player, self.state.auction_skipped)
        self.assertIn("out", self.header_row(out_player)["classes"])

    # A different winner leaves the selector active; the buyer sits out later auctions.
    def test_selector_continues_after_another_player_wins(self):
        self.state.cycles = 1
        p1, p2, p3, p4 = self.state.player_turn_order
        self.state.current_player = p2
        plant_id = self.state.power_plant_market[0]
        second_plant_id = self.state.power_plant_market[1]
        starting_money = self.state.player_money[p3]

        self.assertEqual(self.post("/api/plant/select", plant_id=plant_id), 200)
        self.assertEqual(self.state.auction_bids, {p2: plant_id})
        self.assertEqual(self.state.current_player, p3)

        self.assertEqual(self.post("/api/bid", player=p3, amount=plant_id + 4), 200)

        for player in (p4, p1, p2):
            self.assertEqual(self.post("/api/bid/pass", player=player), 200)

        owned_ids = [plant["plant_id"] for plant in self.state.player_power_plants[p3]]

        self.assertEqual(self.state.player_money[p3], starting_money - plant_id - 4)
        self.assertIn(plant_id, owned_ids)
        self.assertNotIn(plant_id, self.state.power_plant_market)
        self.assertEqual(self.state.current_action, POWER_PLANT_AUCTION)
        self.assertEqual(self.state.current_player, p2)

        self.assertEqual(self.post("/api/plant/select", plant_id=second_plant_id), 200)
        self.assertNotIn(p3, self.state.auction_participants)

    def test_bidding_uses_clockwise_roster_order_not_selector_order(self):
        self.state.cycles = 1
        self.state.player_turn_order = ["p3", "p1", "p4", "p2"]
        selector = "p3"
        plant_id = self.state.power_plant_market[0]
        self.state.current_player = selector

        self.assertEqual(self.post("/api/plant/select", plant_id=plant_id), 200)
        self.assertEqual(self.state.current_player, "p4")

        header = self.client.get("/api/view").get_json()["header"]["turn_order"]
        self.assertEqual([row["label"] for row in header], [self.state.player_aliases[player] for player in self.state.player_turn_order])
        self.assertTrue(next(row["current"] for row in header if row["label"] == self.state.player_aliases["p4"]))

        self.assertEqual(self.post("/api/bid/pass", player="p4"), 200)
        self.assertEqual(self.state.current_player, "p1")
        self.assertEqual(self.post("/api/bid", player="p1", amount=plant_id + 1), 200)
        self.assertEqual(self.state.current_player, "p2")
        self.assertEqual(self.post("/api/bid/pass", player="p2"), 200)
        self.assertEqual(self.state.current_player, selector)
        self.assertEqual(self.post("/api/bid/pass", player=selector), 200)

        self.assertIn("p1", self.state.players_bought_power_plant)
        self.assertEqual(self.state.current_action, POWER_PLANT_AUCTION)
        self.assertEqual(self.state.current_player, selector)

    # A winner with full plant slots must discard one before the auction resumes.
    def test_full_plant_slots_require_discard(self):
        self.state.cycles = 1
        p1, p2, p3, p4 = self.state.player_turn_order
        existing_plant_ids = [31, 46, 50]

        # The plants p2 already owns cannot also be in the draw pile.
        self.state.power_plant_deck = [
            plant_id for plant_id in self.state.power_plant_deck
            if plant_id not in existing_plant_ids
        ]
        self.state.player_power_plants[p2] = [new_power_plant(plant_id) for plant_id in existing_plant_ids]
        plant_id = self.state.power_plant_market[0]
        discarded_plant_id = 31

        self.assertEqual(self.post("/api/plant/select", plant_id=plant_id), 200)
        self.assertEqual(self.post("/api/bid", player=p2, amount=plant_id + 1), 200)

        for player in (p3, p4, p1):
            self.assertEqual(self.post("/api/bid/pass", player=player), 200)

        self.assertEqual(self.state.current_action, DISCARD_POWER_PLANT)
        self.assertEqual(self.state.pending_plant_replacement["plant_id"], plant_id)
        self.assertEqual(len(self.state.player_power_plants[p2]), 3)
        self.assertNotIn("finished", self.header_row(p2)["classes"])

        # Only the winner can discard, and only their own plants.
        view = self.client.get("/api/view").get_json()
        p2_view = find_by_label(view["players"], self.state.player_aliases[p2])
        p1_view = find_by_label(view["players"], self.state.player_aliases[p1])

        self.assertTrue(all(plant["discardable"] for plant in p2_view["plant_slots"]))
        self.assertFalse(any(plant.get("discardable") for plant in p1_view["plant_slots"]))
        self.assertEqual(self.post("/api/plant/discard", player=p2, plant_id=plant_id), 400)

        self.assertEqual(self.post("/api/plant/discard", player=p2, plant_id=discarded_plant_id), 200)

        owned_ids = [plant["plant_id"] for plant in self.state.player_power_plants[p2]]

        self.assertNotIn(discarded_plant_id, owned_ids)
        self.assertIn(plant_id, owned_ids)
        self.assertEqual(len(owned_ids), 3)
        self.assertEqual(self.state.current_action, POWER_PLANT_AUCTION)
        self.assertEqual(self.state.current_player, p1)
        self.assertIn("finished", self.header_row(p2)["classes"])

        for player in (p1, p3, p4):
            self.assertEqual(self.post("/api/bid/pass", player=player), 200)

        # The next phase starts without completion marks.
        header = self.client.get("/api/view").get_json()["header"]["turn_order"]

        self.assertEqual(self.state.current_action, BUYING_RESOURCES)
        self.assertEqual(self.state.phase, 3)
        self.assertTrue(all("finished" not in player["classes"] for player in header))

    # Passing on selection through the whole turn order starts resource buying.
    def test_cycle_zero_selectors_cannot_pass_on_selection(self):
        current = self.state.current_player
        current_view = find_by_label(
            self.client.get("/api/view").get_json()["players"],
            self.state.player_aliases[current],
        )

        self.assertTrue(current_view["bid"]["pass_disabled"])
        self.assertEqual(self.post("/api/bid/pass", player=current), 400)
        self.assertEqual(self.state.current_player, current)
        self.assertFalse(self.state.auction_skipped)

    # Later cycles permit every selector to pass, ending the auction phase.
    def test_all_selectors_pass(self):
        self.state.cycles = 1

        for player in self.state.player_turn_order:
            self.assertEqual(self.post("/api/bid/pass", player=player), 200)

        self.assertEqual(self.state.current_action, BUYING_RESOURCES)
        self.assertEqual(self.state.phase, 3)
        self.assertIsNone(self.state.selected_power_plant)
        self.assertFalse(self.state.players_bought_power_plant)

    # Later cycles allow every remaining selector to pass and end the auction.
    def test_later_cycle_all_selectors_pass(self):
        self.state.cycles = 1

        for player in self.state.player_turn_order:
            self.assertEqual(self.post("/api/bid/pass", player=player), 200)

        self.assertEqual(self.state.current_action, BUYING_RESOURCES)
        self.assertEqual(self.state.phase, 3)
        self.assertIsNone(self.state.selected_power_plant)
        self.assertFalse(self.state.players_bought_power_plant)

    # A player cannot select a plant they cannot afford.
    def test_cannot_select_plant_above_money(self):
        player = self.state.current_player
        plant_id = self.state.power_plant_market[0]
        self.state.player_money[player] = plant_id - 1

        self.assertEqual(self.post("/api/plant/select", plant_id=plant_id), 400)
        self.assertEqual(self.state.current_action, POWER_PLANT_AUCTION)

    # A bid must be higher than the highest bid and within the player's money.
    def test_invalid_bids_are_rejected(self):
        p1, p2, _, _ = self.state.player_turn_order
        plant_id = self.state.power_plant_market[0]
        self.assertEqual(self.post("/api/plant/select", plant_id=plant_id), 200)

        self.assertEqual(self.post("/api/bid", player=p2, amount=plant_id), 400)
        self.assertEqual(self.post("/api/bid", player=p2, amount=self.state.player_money[p2] + 1), 400)
        self.assertEqual(self.post("/api/bid", player=p2, amount=True), 400)
        self.assertEqual(self.post("/api/bid", player=p1, amount=plant_id + 1), 400)

    # A stale player cannot invoke a turn-ending board action.
    def test_stale_player_cannot_end_turn(self):
        current_player = self.state.current_player
        stale_player = self.state.player_turn_order[-1]

        self.assertEqual(self.post("/api/buy-houses", player=stale_player), 400)
        self.assertEqual(self.state.current_player, current_player)

    # Resource and house actions record completion under separate phase keys.
    def test_completion_markers_are_scoped_to_phase(self):
        p1, p2, _, _ = self.state.player_turn_order
        self.state.current_action = BUYING_RESOURCES

        self.assertEqual(self.post("/api/buy-resources", player=p1, resources={}), 200)
        self.assertEqual(self.state.phase_finished_players[PHASE_THREE_RESOURCE_BUYING], [p1])

        self.state.current_action = "building_houses"
        self.state.current_player = p2

        self.assertEqual(self.post("/api/buy-houses", player=p2), 200)
        self.assertEqual(self.state.phase_finished_players[PHASE_FOUR_BUILDING_HOUSES], [p2])
        self.assertNotIn("finished", self.header_row(p1)["classes"])
        self.assertIn("finished", self.header_row(p2)["classes"])


if __name__ == "__main__":
    unittest.main()
