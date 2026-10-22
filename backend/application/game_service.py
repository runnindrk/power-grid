# -------------------------------------------------------------------------------------------------
# Imports

from copy import deepcopy
from threading import RLock

from backend.data.files import load_plant_deck, load_resources
from backend.rules.common.error_codes import ErrorCode
from backend.rules.common.phase_state import mark_phase_finished, phase_key
from backend.rules.common.resource_transfer import (
    find_player_plant,
    transfer_plant_resource,
)
from backend.rules.phase_five_bureaucracy.bureaucracy import bureaucracy
from backend.rules.phase_four_building_houses.building_houses import buy_houses
from backend.rules.phase_three_resource_buying.resource_buying import buy_resources, quote_resources
from backend.rules.phase_two_auction.auction import (
    discard_power_plant,
    pass_bid,
    place_bid,
    select_power_plant,
)
from backend.rules.phase_two_auction.turn_order import advance_turn

# -------------------------------------------------------------------------------------------------
# Application service

class GameService:
    """Coordinate game rules, turn checks, state access, and save requests."""

    def __init__(self, state, save_state, plant_slots_per_player=3):
        self._state = state
        self._save_state = save_state
        self._plant_slots_per_player = plant_slots_per_player
        self._lock = RLock()

    def snapshot(self):
        with self._lock:
            return deepcopy(self._state)

    def save_game(self):
        with self._lock:
            self._save_state(self._state)

    def _current_player_action(self, player, action):
        with self._lock:
            # Reject stale requests before a rule can mutate the game state.
            if player != self._state.current_player or player not in self._state.player_turn_order:
                return ErrorCode.E_NOT_OKAY

            phase = phase_key(self._state.current_action)
            code = action(self._state)
            if code == ErrorCode.E_OK:
                mark_phase_finished(self._state, phase, player)
                return advance_turn(self._state, player)

            return code

    def toggle_house_spot(self, city, spot):
        with self._lock:
            spots = self._state.map_houses.get(city)
            if spots is None or spot not in spots or spots[spot] is not None:
                return ErrorCode.E_NOT_OKAY

            selection = {"city": city, "spot": spot}
            if selection in self._state.pending_houses:
                self._state.pending_houses.remove(selection)
            else:
                self._state.pending_houses.append(selection)

            return ErrorCode.E_OK

    def toggle_ready_to_power(self, player, plant_id):
        with self._lock:
            plant = find_player_plant(self._state, player, plant_id)
            if plant is None:
                return ErrorCode.E_NOT_OKAY

            plant["ready_to_power"] = not plant["ready_to_power"]
            return ErrorCode.E_OK

    def transfer_resource(
        self,
        player,
        source_plant_id,
        source_slot,
        target_plant_id,
        target_slot,
    ):
        with self._lock:
            return transfer_plant_resource(
                self._state,
                player,
                source_plant_id,
                source_slot,
                target_plant_id,
                target_slot,
                load_plant_deck(),
                load_resources()["resources"],
            )

    def select_power_plant(self, plant_id):
        with self._lock:
            return select_power_plant(self._state, plant_id, self._plant_slots_per_player)

    def place_bid(self, player, amount):
        with self._lock:
            return place_bid(self._state, player, amount, self._plant_slots_per_player)

    def pass_bid(self, player):
        with self._lock:
            return pass_bid(self._state, player, self._plant_slots_per_player)

    def discard_power_plant(self, player, plant_id):
        with self._lock:
            return discard_power_plant(self._state, player, plant_id)

    def quote_resources(self, player, resources):
        with self._lock:
            return quote_resources(self._state, player, resources)

    def buy_resources(self, player, resources):
        return self._current_player_action(
            player,
            lambda state: buy_resources(state, player, resources),
        )

    def buy_houses(self, player):
        def buy_selected_houses(state):
            return buy_houses(state, player, state.pending_houses)

        return self._current_player_action(
            player,
            buy_selected_houses,
        )

    def bureaucracy(self, player):
        return self._current_player_action(player, bureaucracy)