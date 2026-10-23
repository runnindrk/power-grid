# Running Tests

From the repository root, run the full test suite with:

```sh
python3 -m unittest discover -v
```

## How the tests are organized

| File | What it covers |
| --- | --- |
| `tests/helpers.py` | Shared setup: a fresh state, a game service that does not save, a Flask test client |
| `tests/test_auction_workflow.py` | Selecting, bidding, passing and discarding through the HTTP routes |
| `tests/test_game_cycles.py` | Phase one to five, turn order between cycles, header labels |
| `tests/test_game_setup.py` | Fresh game creation, player count validation, explicit loading, and timestamped save listing |
| `tests/test_map_areas.py` | Connected region selection and inactive area enforcement |
| `tests/test_plant_deck.py` | Starting deck, market refill, next card back |
| `tests/test_player_colors.py` | Player colors stay the same when the turn order changes |
| `tests/test_rules_common.py` | Turn order, phase markers, owned plants, moving fuel |

Tests that exercise game routes provide in-memory load/save callbacks so the real save game is never changed.
