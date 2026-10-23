import random
import unittest

from backend.application.game_service import GameService
from backend.data.files import load_settings
from backend.game_setup.new_game import create_new_game_state
from backend.rules.common.constants import BUILDING_HOUSES, BUYING_RESOURCES
from backend.rules.common.error_codes import ErrorCode
from backend.rules.common.phase_flow import start_phase_three
from backend.rules.common.player_plants import new_power_plant
from backend.server.app import create_app
from backend.views.game_view import build_view


class ResourceBuyingTests(unittest.TestCase):
    def setUp(self):
        self.state = create_new_game_state(2, rng=random.Random(19))
        self.state.current_action = BUYING_RESOURCES
        self.state.current_player = self.state.player_turn_order[-1]
        self.player = self.state.current_player
        self.state.player_power_plants[self.player] = [new_power_plant(4), new_power_plant(5)]
        self.service = GameService(self.state, lambda saved: None)
        self.client = create_app(self.service).test_client()

    @staticmethod
    def quantities(coal=0, oil=0, trash=0, uranium=0):
        return {
            "coal": str(coal),
            "oil": str(oil),
            "trash": str(trash),
            "uranium": str(uranium),
        }

    def quote(self, **quantities):
        return self.client.post(
            "/api/resource-price",
            json={"player": self.player, "resources": self.quantities(**quantities)},
        )

    def test_quote_reserves_stock_and_prices_the_next_filled_boxes(self):
        response = self.quote(coal=4, oil=2)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["price_label"], "$11")
        self.assertEqual(self.state.resource_market["coal"], 20)
        self.assertEqual(self.state.resource_market["oil"], 16)
        self.assertEqual(
            self.state.pending_resource_purchase,
            {"coal": 4, "oil": 2, "trash": 0, "uranium": 0},
        )

        view = build_view(self.state)
        player_view = next(row for row in view["players"] if row["player"] == self.player)
        self.assertEqual(player_view["resource_buy"]["price_label"], "$11")
        self.assertEqual(
            {row["resource"]: row["quantity"] for row in player_view["resource_buy"]["rows"]},
            {"coal": 4, "oil": 2, "trash": 0, "uranium": 0},
        )

    def test_edit_releases_old_reservation_and_invalid_edit_is_atomic(self):
        first = self.quote(coal=3)
        self.assertEqual(first.get_json()["price_label"], "$3")
        self.assertEqual(self.state.resource_market["coal"], 21)

        revised = self.quote(coal=4)
        self.assertEqual(revised.get_json()["price_label"], "$5")
        self.assertEqual(self.state.resource_market["coal"], 20)

        invalid = self.quote(coal=9)
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(self.state.resource_market["coal"], 20)
        self.assertEqual(self.state.pending_resource_purchase["coal"], 4)

    def test_buy_deducts_money_and_distributes_fuel_to_compatible_plants(self):
        request = self.quantities(coal=4, oil=2)
        self.assertEqual(self.quote(coal=4, oil=2).get_json()["price_label"], "$11")

        response = self.client.post(
            "/api/buy-resources",
            json={"player": self.player, "resources": request},
        )

        self.assertEqual(response.status_code, 200)
        coal_plant, hybrid_plant = self.state.player_power_plants[self.player]
        self.assertEqual(coal_plant["resources"]["coal"], 4)
        self.assertEqual(hybrid_plant["resources"]["oil"], 2)
        self.assertEqual(self.state.player_money[self.player], 39)
        self.assertEqual(self.state.resource_market["coal"], 20)
        self.assertEqual(self.state.resource_market["oil"], 16)
        self.assertFalse(self.state.pending_resource_purchase)
        self.assertIsNone(self.state.pending_resource_player)

    def test_unstoreable_or_unaffordable_selection_does_not_reserve_stock(self):
        self.state.player_power_plants[self.player] = [new_power_plant(4)]
        market_before = dict(self.state.resource_market)

        self.assertEqual(self.quote(oil=1).status_code, 400)
        self.assertEqual(self.state.resource_market, market_before)
        self.assertFalse(self.state.pending_resource_purchase)

        self.state.player_money[self.player] = 2
        self.assertEqual(self.quote(coal=3).status_code, 400)
        self.assertEqual(self.state.resource_market, market_before)
        self.assertFalse(self.state.pending_resource_purchase)

    def test_resource_phase_starts_and_advances_in_reverse_without_mutating_roster(self):
        order = list(self.state.player_turn_order)
        start_phase_three(self.state)

        self.assertEqual(self.state.current_player, order[-1])
        header = build_view(self.state)["header"]
        header_order = [row["label"] for row in header["turn_order"]]
        self.assertEqual(header_order, [self.state.player_aliases[player] for player in order])
        self.assertTrue(header["reverse_turn_direction"])

        service = GameService(self.state, lambda saved: None)

        for expected_player in reversed(order):
            self.assertEqual(service.buy_resources(expected_player, {}), ErrorCode.E_OK)

        self.assertEqual(self.state.current_action, BUILDING_HOUSES)
        self.assertEqual(self.state.player_turn_order, order)


if __name__ == "__main__":
    unittest.main()