import unittest

from backend.rules.common.constants import (
    BUYING_RESOURCES,
    DISCARD_POWER_PLANT,
    POWER_PLANT_AUCTION,
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

    # A different winner leaves the selector active; the buyer sits out later auctions.
    def test_selector_continues_after_another_player_wins(self):
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

    # A winner with full plant slots must discard one before the auction resumes.
    def test_full_plant_slots_require_discard(self):
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
    def test_all_selectors_pass(self):
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
