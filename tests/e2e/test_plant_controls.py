from backend.game_setup.new_game import create_new_game_state
from backend.rules.common.constants import BUREAUCRACY
from backend.rules.common.player_plants import new_power_plant
from tests.e2e.support import BrowserGameTestCase


class PlantControlsE2ETests(BrowserGameTestCase):
    def test_ready_button_is_disabled_when_fuel_is_insufficient(self):
        state = create_new_game_state(2)
        player = state.current_player
        plant = new_power_plant(4)
        plant["resources"]["coal"] = 1
        state.player_power_plants[player] = [plant]
        state.phase = 5
        state.current_action = BUREAUCRACY
        self.open_game(state)

        button = self.page.locator(
            f'.player-row[data-player-id="{player}"] [data-plant-id="4"] .plant-ready-button'
        )

        self.assertTrue(button.is_disabled())
        self.assert_no_page_errors()

    def test_dragging_fuel_onto_occupied_slot_swaps_it(self):
        state = create_new_game_state(2)
        player = state.current_player
        coal_plant = new_power_plant(5)
        oil_plant = new_power_plant(12)
        coal_plant["resources"]["coal"] = 1
        oil_plant["resources"]["oil"] = 1
        state.player_power_plants[player] = [coal_plant, oil_plant]
        self.open_game(state)

        row = self.page.locator(f'.player-row[data-player-id="{player}"]')
        source = row.locator('[data-plant-id="5"] .plant-storage-slot.filled').first
        target = row.locator('[data-plant-id="12"] .plant-storage-slot.filled').first

        with self.page.expect_response(
            lambda response: response.url.endswith("/api/transfer-plant-resource")
            and response.request.method == "POST",
        ) as transfer_response:
            source.drag_to(target)

        self.assertEqual(transfer_response.value.status, 200)
        self.assertEqual(transfer_response.value.json()["status"], "ok")
        self.assertEqual(coal_plant["resources"]["coal"], 0)
        self.assertEqual(coal_plant["resources"]["oil"], 1)
        self.assertEqual(oil_plant["resources"]["oil"], 0)
        self.assertEqual(oil_plant["resources"]["coal"], 1)
        self.assert_no_page_errors()

    def test_moving_fuel_from_ready_plant_turns_it_off_and_blocks_reenable(self):
        state = create_new_game_state(2)
        player = state.current_player
        source_plant = new_power_plant(4)
        target_plant = new_power_plant(10)
        source_plant["resources"]["coal"] = 2
        source_plant["ready_to_power"] = True
        state.player_power_plants[player] = [source_plant, target_plant]
        self.open_game(state)

        row = self.page.locator(f'.player-row[data-player-id="{player}"]')
        source = row.locator('[data-plant-id="4"] .plant-storage-slot.filled').first
        target = row.locator('[data-plant-id="10"] .plant-storage-slot:not(.filled)').first

        with self.page.expect_response(
            lambda response: response.url.endswith("/api/view")
            and response.request.method == "GET",
        ), self.page.expect_response(
            lambda response: response.url.endswith("/api/transfer-plant-resource")
            and response.request.method == "POST",
        ) as transfer_response:
            source.drag_to(target)

        self.assertEqual(transfer_response.value.status, 200)
        self.assertFalse(source_plant["ready_to_power"])
        button = row.locator('[data-plant-id="4"] .plant-ready-button')
        self.assertTrue(button.is_disabled())
        self.assertEqual(button.get_attribute("aria-pressed"), "false")
        self.assert_no_page_errors()
