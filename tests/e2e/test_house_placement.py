from backend.game_setup.new_game import create_new_game_state
from backend.rules.common.constants import BUILDING_HOUSES
from tests.e2e.support import BrowserGameTestCase


class HousePlacementE2ETests(BrowserGameTestCase):
    def open_house_phase(self, state=None):
        if state is None:
            state = create_new_game_state(2)

        state.phase = 4
        state.current_action = BUILDING_HOUSES
        self.open_game(state)

    def test_spot_click_selects_and_deselects_through_api(self):
        self.open_house_phase()
        spot = self.page.locator('.house-spot[aria-disabled="false"]').first

        with self.page.expect_response(
            lambda response: response.url.endswith("/api/view")
            and response.request.method == "GET",
        ), self.page.expect_response(
            lambda response: response.url.endswith("/api/house-spot")
            and response.request.method == "POST",
        ) as selected_response:
            spot.click()

        self.assertEqual(selected_response.value.status, 200)
        self.assertEqual(selected_response.value.json()["status"], "ok")
        self.page.wait_for_function("() => document.querySelectorAll('.house-spot.selected').length === 1")
        self.assertEqual(self.page.locator(".house-spot.selected").count(), 1)
        self.assertEqual(
            self.page.locator(".house-spot.selected .house-spot-face").get_attribute("fill"),
            "url(#selected-house-pattern)",
        )

        selected_spot = self.page.locator(".house-spot.selected")

        with self.page.expect_response(
            lambda response: response.url.endswith("/api/view")
            and response.request.method == "GET",
        ), self.page.expect_response(
            lambda response: response.url.endswith("/api/house-spot")
            and response.request.method == "POST",
        ) as deselected_response:
            selected_spot.click()

        self.assertEqual(deselected_response.value.status, 200)
        self.page.wait_for_function("() => document.querySelectorAll('.house-spot.selected').length === 0")
        self.assertEqual(self.page.locator(".house-spot.selected").count(), 0)
        self.assert_no_page_errors()

    def test_hover_quote_shows_spot_plus_connection_price(self):
        state = create_new_game_state(4)
        state.regions_chosen = ["green", "orange", "red", "yellow"]
        state.step = 3
        player = state.current_player
        state.map_houses["Flensburg"]["spot_1"] = player
        self.open_house_phase(state)
        spot = self.page.locator('[aria-label^="Kiel, spot 2"]')

        spot.hover()
        tooltip = self.page.locator("#tooltip")

        self.assertEqual(tooltip.text_content(), "$15 + $4 connection = $19")
        self.assertGreater(self.page.locator(".connection-line.network-highlight").count(), 0)
        self.assert_no_page_errors()

    def test_bought_house_keeps_connection_route_visible(self):
        state = create_new_game_state(4)
        state.regions_chosen = ["green", "orange", "red", "yellow"]
        state.step = 3
        player = state.current_player
        state.map_houses["Flensburg"]["spot_1"] = player
        self.open_house_phase(state)
        spot = self.page.locator('[aria-label^="Kiel, spot 1"]')

        with self.page.expect_response(
            lambda response: response.url.endswith("/api/view")
            and response.request.method == "GET",
        ), self.page.expect_response(
            lambda response: response.url.endswith("/api/house-spot")
            and response.request.method == "POST",
        ):
            spot.click()

        row = self.page.locator(f'.player-row[data-player-id="{player}"]')

        with self.page.expect_response(
            lambda response: response.url.endswith("/api/view")
            and response.request.method == "GET",
        ), self.page.expect_response(
            lambda response: response.url.endswith("/api/buy-houses")
            and response.request.method == "POST",
        ) as purchase_response:
            row.locator(".player-buy-houses-button").click()

        self.assertEqual(purchase_response.value.status, 200)
        self.page.wait_for_function("() => document.querySelectorAll('.connection-line.network-segment').length > 0")
        self.assertGreater(self.page.locator(".connection-line.network-segment").count(), 0)
        self.assert_no_page_errors()

    def test_locked_spot_does_not_send_a_request(self):
        self.open_house_phase()
        requests = []
        self.page.on("request", lambda request: requests.append(request.url))
        locked_spot = self.page.locator('.house-spot.locked[aria-disabled="true"]').first

        self.assertTrue(locked_spot.is_visible())
        locked_spot.click(force=True)

        self.assertFalse(any(url.endswith("/api/house-spot") for url in requests))
        self.assert_no_page_errors()

    def test_buy_button_purchases_selected_house(self):
        self.open_house_phase()
        spot = self.page.locator('.house-spot[aria-disabled="false"]').first

        with self.page.expect_response(
            lambda response: response.url.endswith("/api/view")
            and response.request.method == "GET",
        ), self.page.expect_response(
            lambda response: response.url.endswith("/api/house-spot")
            and response.request.method == "POST",
        ):
            spot.click()

        current_player = next(
            player for player in self.fetch_view()["players"]
            if player["is_current_player"]
        )
        button = self.page.locator(
            f'.player-row[data-player-id="{current_player["player"]}"] .player-buy-houses-button'
        )

        self.assertFalse(button.is_disabled())

        with self.page.expect_response(
            lambda response: response.url.endswith("/api/view")
            and response.request.method == "GET",
        ), self.page.expect_response(
            lambda response: response.url.endswith("/api/buy-houses")
            and response.request.method == "POST",
        ) as purchase_response:
            button.click()

        self.assertEqual(purchase_response.value.status, 200)
        self.assertEqual(purchase_response.value.json()["status"], "ok")
        self.page.wait_for_function("() => document.querySelectorAll('.house-spot.occupied').length === 1")
        self.assertEqual(self.page.locator(".house-spot.occupied").count(), 1)
        self.assertEqual(self.page.locator(".house-spot.selected").count(), 0)
        self.assert_no_page_errors()
