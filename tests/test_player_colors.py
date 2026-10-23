import unittest

from backend.data.game_state_store import load_game_state
from backend.views.game_view import build_view


def colors_by_player(view):
    """Return the color of every player row in the view."""
    colors = {}

    for row in view["players"]:
        colors[row["player"]] = row["color"]

    return colors


def row_order(view):
    """Return the players in the order of the player board."""
    return [row["player"] for row in view["players"]]


class PlayerColorTests(unittest.TestCase):
    # Player colors stay tied to the player after the turn order changes.
    def test_colors_stay_with_players_after_turn_order_shuffle(self):
        state = load_game_state()
        before = build_view(state)

        state.player_turn_order.reverse()
        after = build_view(state)

        turn_order_labels = [player["label"] for player in after["header"]["turn_order"]]
        expected_labels = [state.player_aliases[player] for player in state.player_turn_order]

        self.assertEqual(colors_by_player(after), colors_by_player(before))
        self.assertEqual(row_order(after), row_order(before))
        self.assertEqual(turn_order_labels, expected_labels)

    # Older saves without colors use the stable player roster as a fallback.
    def test_legacy_state_uses_stable_roster_colors(self):
        state = load_game_state()
        state.player_colors = {}
        before = build_view(state)

        state.player_turn_order.reverse()
        after = build_view(state)

        self.assertEqual(colors_by_player(after), colors_by_player(before))
        self.assertEqual(row_order(after), row_order(before))


if __name__ == "__main__":
    unittest.main()
