from backend.game_setup.new_game import create_new_game_state
from backend.rules.common.constants import BUYING_RESOURCES
from backend.rules.common.player_plants import new_power_plant
from tests.e2e.support import BrowserGameTestCase


class ResourcePurchaseE2ETests(BrowserGameTestCase):
    def test_quote_and_buy_resources_from_player_board(self):
        state = create_new_game_state(2)
        player = state.player_turn_order[-1]
        state.phase = 3
        state.current_action = BUYING_RESOURCES
        state.current_player = player
        state.player_power_plants[player] = [new_power_plant(4)]
        starting_money = state.player_money[player]
        self.open_game(state)

        row = self.page.locator(f'.player-row[data-player-id="{player}"]')
        coal_input = row.get_by_label(f"Coal quantity for {state.player_aliases[player]}")

        with self.page.expect_response(
            lambda response: response.url.endswith("/api/resource-price")
            and response.request.method == "POST",
        ) as quote_response:
            coal_input.fill("2")

        self.assertEqual(quote_response.value.status, 200)
        self.assertEqual(quote_response.value.json()["price_label"], "$2")
        self.assertEqual(row.locator(".resource-buy-total").text_content(), "$2")

        with self.page.expect_response(
            lambda response: response.url.endswith("/api/buy-resources")
            and response.request.method == "POST",
        ) as purchase_response:
            row.locator(".resource-buy-button").click()

        self.assertEqual(purchase_response.value.status, 200)
        self.assertEqual(state.player_money[player], starting_money - 2)
        self.assertEqual(state.player_power_plants[player][0]["resources"]["coal"], 2)
        self.assertEqual(row.locator(".plant-storage-slot.filled").count(), 2)
        self.assert_no_page_errors()
