import random

from backend.rules.common.error_codes import ErrorCode
from backend.rules.common.game_state import GameState
from backend.rules.common.phase_state import clear_phase_finished


def determine_initial_order(state: GameState, rng=None):
	"""Determine the pre-auction order and start phase two."""
	if state.current_action != "determining_player_order" or not state.player_turn_order:
		return ErrorCode.E_NOT_OKAY

	if state.cycles == 0:
		randomizer = rng if rng is not None else random
		randomizer.shuffle(state.player_turn_order)
	else:
		determine_order_by_houses_and_plant(state)

	state.current_player = state.player_turn_order[0]
	state.current_action = "power_plant_auction"
	state.phase = 2
	clear_phase_finished(state, "phase_one_turn_order")

	return ErrorCode.E_OK


def determine_order_after_first_auction(state):
	"""Order cycle-zero players by highest plant before resource buying."""
	if not state.player_turn_order:
		return ErrorCode.E_NOT_OKAY

	state.player_turn_order.sort(
		key=lambda player: _highest_plant_id(state, player),
		reverse=True,
	)
	state.current_player = state.player_turn_order[0]
	state.current_action = "buying_resources"
	state.phase = 3

	return ErrorCode.E_OK


def determine_order_by_houses_and_plant(state):
	"""Sort players by house count, then highest plant, preserving ties."""
	house_counts = {
		player: _count_houses(state, player)
		for player in state.player_turn_order
	}
	state.player_turn_order.sort(
		key=lambda player: (
			house_counts[player],
			_highest_plant_id(state, player),
		),
		reverse=True,
	)


def _highest_plant_id(state: GameState, player):
	return max(
		(plant["plant_id"] for plant in state.player_power_plants.get(player, [])),
		default=0,
	)


def _count_houses(state: GameState, player):
	return sum(
		owner == player
		for city_spots in state.map_houses.values()
		for owner in city_spots.values()
	)