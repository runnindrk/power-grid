import threading
import unittest
from unittest.mock import patch

from werkzeug.serving import make_server

from backend.application.game_service import GameService
from backend.server.app import create_app

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


@unittest.skipIf(sync_playwright is None, "Install requirements-test.txt to run browser tests.")
class BrowserGameTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.page = self.browser.new_page()
        self.page_errors = []
        self.page.on("pageerror", lambda error: self.page_errors.append(error.message))
        self.server = None
        self.server_thread = None
        self.state = None
        self.saved_games_patch = None

    def tearDown(self):
        self.page.close()

        if self.server is not None:
            self.server.shutdown()
            self.server_thread.join(timeout=5)
            self.server.server_close()

        if self.saved_games_patch is not None:
            self.saved_games_patch.stop()

    def open_game(self, state=None, start_new_game=True, load_state=None, saved_games=None):
        self.state = state
        save_without_disk_io = lambda saved_state: None
        service = GameService(state, save_without_disk_io) if state is not None else None
        self.saved_games_patch = patch(
            "backend.server.routes.list_saved_games",
            return_value=saved_games or [],
        )
        self.saved_games_patch.start()
        app = create_app(
            game_service=service,
            load_state=load_state,
            save_state=save_without_disk_io,
        )
        self.server = make_server("127.0.0.1", 0, app, threaded=True)
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"
        self.page.goto(self.base_url)

        if state is None and start_new_game:
            self.page.get_by_role("button", name="New Game").click()
            self.page.wait_for_url("**/ui/map.html")

        self.page.wait_for_load_state("networkidle")

    def fetch_view(self):
        return self.page.evaluate("async () => (await fetch('/api/view')).json()")

    def assert_no_page_errors(self):
        self.assertEqual(self.page_errors, [])
