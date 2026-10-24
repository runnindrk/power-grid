from datetime import datetime, timezone

from backend.game_setup.new_game import create_new_game_state
from tests.e2e.support import BrowserGameTestCase


class SetupE2ETests(BrowserGameTestCase):
    def test_new_game_form_creates_custom_player_roster(self):
        self.open_game(start_new_game=False)
        self.page.get_by_label("Number of Players").fill("2")
        self.page.get_by_label("Alias for player 1").fill("North")
        self.page.get_by_label("Alias for player 2").fill("South")

        with self.page.expect_response(
            lambda response: response.url.endswith("/api/new-game")
            and response.request.method == "POST",
        ) as new_game_response:
            self.page.get_by_role("button", name="New Game").click()

        self.assertEqual(new_game_response.value.status, 200)
        self.page.wait_for_url("**/ui/map.html")
        self.page.wait_for_load_state("networkidle")
        self.assertEqual(self.page.locator(".player-row").count(), 2)
        self.assertEqual(
            self.page.locator(".player-name").all_text_contents(),
            ["North", "South"],
        )
        self.assert_no_page_errors()

    def test_saved_game_button_loads_fixture_without_disk_access(self):
        saved_state = create_new_game_state(2)
        save_id = "fixture-save.json"
        saved_games = [{
            "id": save_id,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "number_of_players": 2,
        }]
        self.open_game(
            start_new_game=False,
            load_state=lambda requested_id: saved_state if requested_id == save_id else None,
            saved_games=saved_games,
        )

        with self.page.expect_response(
            lambda response: response.url.endswith("/api/load-game")
            and response.request.method == "POST",
        ) as load_response:
            self.page.locator(".saved-game-load").click()

        self.assertEqual(load_response.value.status, 200)
        self.page.wait_for_url("**/ui/map.html")
        self.page.wait_for_load_state("networkidle")
        self.assertEqual(self.page.locator(".player-row").count(), 2)
        self.assert_no_page_errors()

    def test_save_button_posts_without_writing_a_real_save(self):
        self.open_game(create_new_game_state(2))

        with self.page.expect_response(
            lambda response: response.url.endswith("/api/save-game")
            and response.request.method == "POST",
        ) as save_response:
            self.page.get_by_role("button", name="Save game").click()

        self.assertEqual(save_response.value.status, 200)
        self.assertEqual(save_response.value.json()["status"], "ok")
        self.assert_no_page_errors()
