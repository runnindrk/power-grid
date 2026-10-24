# Running Tests

From the repository root, run the fast unit suite with:

```sh
python3 -m unittest discover -s tests/unit -v
```

## Browser tests

The Playwright suite runs each scenario against an isolated in-process Flask server and a fresh game state. Its save callback is a no-op, so browser tests never write to `game_info/game_save`.

Install the test dependencies and Chromium once:

```sh
python3 -m pip install -r requirements-test.txt
python3 -m playwright install chromium
```

Run browser tests with:

```sh
python3 -m unittest discover -s tests/e2e -v
```

Run both suites together with:

```sh
python3 -m unittest discover -v
```

## Layout

- `tests/unit/` contains fast rule, service, and Flask test-client tests. Shared fixtures live in `tests/unit/helpers.py`.
- `tests/e2e/` contains Playwright browser tests for custom setup, save/load controls, auction bidding, resource quote and purchase, house selection, hover pricing, route persistence and buying, locked spots, ready-to-power and payout, and resource moves/swaps.
