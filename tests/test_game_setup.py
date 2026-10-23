import unittest

from backend.data.game_state_store import load_game_state
from backend.game_setup.starting_money import STARTING_MONEY, create_initial_player_money


class GameSetupTests(unittest.TestCase):
    def test_starting_money_is_created_for_every_player_and_matches_save(self):
        state = load_game_state()
        expected = {player: STARTING_MONEY for player in state.player_aliases}

        self.assertEqual(STARTING_MONEY, 50)
        self.assertEqual(create_initial_player_money(state.player_aliases), expected)
        self.assertEqual(state.player_money, expected)


if __name__ == "__main__":
    unittest.main()