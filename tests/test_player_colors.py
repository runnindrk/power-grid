import unittest
from copy import deepcopy

from backend.data.game_state_store import load_game_state
from backend.views.game_view import build_view


class PlayerColorTests(unittest.TestCase):
    # Player colors remain tied to identity after the turn order changes.
    def test_colors_stay_with_players_after_turn_order_shuffle(self):
        state = deepcopy(load_game_state())
        original_colors = {
            player["player"]: player["color"]
            for player in build_view(state)["players"]
        }
        original_row_order = [player["player"] for player in build_view(state)["players"]]
        state.player_turn_order.reverse()
        view = build_view(state)
        reordered_colors = {
            player["player"]: player["color"]
            for player in view["players"]
        }
        reordered_row_order = [player["player"] for player in view["players"]]
        turn_order = [player["label"] for player in view["header"]["turn_order"]]

        self.assertEqual(reordered_colors, original_colors)
        self.assertEqual(reordered_row_order, original_row_order)
        self.assertEqual(
            turn_order,
            [state.player_aliases[player] for player in state.player_turn_order],
        )

    # Older saves without a color map use the stable player roster as a fallback.
    def test_legacy_state_uses_stable_roster_colors(self):
        state = deepcopy(load_game_state())
        state.player_colors = {}
        original_colors = {
            player["player"]: player["color"]
            for player in build_view(state)["players"]
        }
        original_row_order = [player["player"] for player in build_view(state)["players"]]
        state.player_turn_order.reverse()
        view = build_view(state)
        reordered_colors = {
            player["player"]: player["color"]
            for player in view["players"]
        }

        self.assertEqual(reordered_colors, original_colors)
        self.assertEqual(
            [player["player"] for player in view["players"]],
            original_row_order,
        )


if __name__ == "__main__":
    unittest.main()