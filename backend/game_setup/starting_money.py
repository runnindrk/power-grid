STARTING_MONEY = 50


def create_initial_player_money(players):
    """Return the starting money balance for each player."""
    return {player: STARTING_MONEY for player in players}