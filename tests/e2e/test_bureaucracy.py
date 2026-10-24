from backend.game_setup.new_game import create_new_game_state
from backend.rules.common.constants import BUREAUCRACY
from backend.rules.common.player_plants import new_power_plant
from tests.e2e.support import BrowserGameTestCase


class BureaucracyE2ETests(BrowserGameTestCase):
    def test_ready_plant_power_action_awards_money_and_resets_controls(self):
        state = create_new_game_state(2)
        player = state.player_turn_order[0]
        state.phase = 5
        state.current_action = BUREAUCRACY
        state.current_player = player
        plant = new_power_plant(4)
        plant["resources"]["coal"] = 2
        state.player_power_plants[player] = [plant]
        state.player_money[player] = 0
        for spots in state.map_houses.values():
            for spot in spots:
                spots[spot] = None
        first_city = next(iter(state.map_houses))
        state.map_houses[first_city]["spot_1"] = player
        self.open_game(state)

        row = self.page.locator(f'.player-row[data-player-id="{player}"]')
        ready_button = row.locator('[data-plant-id="4"] .plant-ready-button')
        self.assertFalse(ready_button.is_disabled())

        with self.page.expect_response(
            lambda response: response.url.endswith("/api/view")
            and response.request.method == "GET",
        ), self.page.expect_response(
            lambda response: response.url.endswith("/api/plant/ready-to-power")
            and response.request.method == "POST",
        ) as ready_response:
            ready_button.click()

        self.assertEqual(ready_response.value.status, 200)
        self.assertTrue(plant["ready_to_power"])

        with self.page.expect_response(
            lambda response: response.url.endswith("/api/view")
            and response.request.method == "GET",
        ), self.page.expect_response(
            lambda response: response.url.endswith("/api/bureaucracy")
            and response.request.method == "POST",
        ) as power_response:
            row.locator(".player-power-button").click()

        self.assertEqual(power_response.value.status, 200)
        self.assertEqual(state.player_money[player], 22)
        self.assertFalse(plant["ready_to_power"])
        power_button = row.locator(".player-power-button")
        power_button.wait_for(state="visible")
        self.assertTrue(power_button.is_disabled())
        self.assert_no_page_errors()
