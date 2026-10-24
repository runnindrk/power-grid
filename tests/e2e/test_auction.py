from backend.game_setup.new_game import create_new_game_state
from backend.rules.common.constants import POWER_PLANT_AUCTION
from tests.e2e.support import BrowserGameTestCase


class AuctionE2ETests(BrowserGameTestCase):
    def test_market_selection_bid_and_pass_awards_plant(self):
        state = create_new_game_state(2)
        state.phase = 2
        state.current_action = POWER_PLANT_AUCTION
        state.cycles = 1
        selector, other_player = state.player_turn_order
        state.current_player = selector
        starting_money = state.player_money[other_player]
        self.open_game(state)

        plant_card = self.page.locator("#power-plant-market .power-plant-card.selectable").first
        plant_id = int(plant_card.get_attribute("data-plant-id"))

        with self.page.expect_response(
            lambda response: response.url.endswith("/api/view")
            and response.request.method == "GET",
        ), self.page.expect_response(
            lambda response: response.url.endswith("/api/plant/select")
            and response.request.method == "POST",
        ) as selection_response:
            plant_card.click()

        self.assertEqual(selection_response.value.status, 200)
        self.assertEqual(state.current_player, other_player)

        bid_row = self.page.locator(f'.player-row[data-player-id="{other_player}"]')
        bid_amount = plant_id + 1
        bid_row.locator(".bid-amount").fill(str(bid_amount))

        with self.page.expect_response(
            lambda response: response.url.endswith("/api/view")
            and response.request.method == "GET",
        ), self.page.expect_response(
            lambda response: response.url.endswith("/api/bid")
            and response.request.method == "POST",
        ) as bid_response:
            bid_row.locator(".bid-submit").click()

        self.assertEqual(bid_response.value.status, 200)
        self.assertEqual(state.current_player, selector)

        selector_row = self.page.locator(f'.player-row[data-player-id="{selector}"]')

        with self.page.expect_response(
            lambda response: response.url.endswith("/api/view")
            and response.request.method == "GET",
        ), self.page.expect_response(
            lambda response: response.url.endswith("/api/bid/pass")
            and response.request.method == "POST",
        ) as pass_response:
            selector_row.locator(".bid-pass").click()

        self.assertEqual(pass_response.value.status, 200)
        self.assertEqual(state.player_money[other_player], starting_money - bid_amount)
        self.assertIn(plant_id, [plant["plant_id"] for plant in state.player_power_plants[other_player]])
        awarded_plant = self.page.locator(
            f'.player-row[data-player-id="{other_player}"] [data-plant-id="{plant_id}"]'
        )
        awarded_plant.wait_for(state="visible")
        self.assertTrue(awarded_plant.is_visible())
        self.assert_no_page_errors()
