# -------------------------------------------------------------------------------------------------
# Imports

from copy import deepcopy
from threading import RLock

from backend.data.files import load_map, load_number_of_areas, load_plant_deck, load_resources
from backend.rules.common.constants import (
    BUILDING_HOUSES,
    BUREAUCRACY,
    BUYING_RESOURCES,
    DETERMINING_PLAYER_ORDER,
    PHASE_FIVE_BUREAUCRACY,
    PHASE_FOUR_BUILDING_HOUSES,
    PHASE_THREE_RESOURCE_BUYING,
)
from backend.rules.common.error_codes import ErrorCode
from backend.rules.common.phase_flow import start_phase_five, start_phase_four
from backend.rules.common.phase_state import (
    all_players_finished,
    clear_phase_finished,
    mark_phase_finished,
    phase_key,
)
from backend.rules.common.player_plants import find_player_plant
from backend.rules.common.resource_transfer import transfer_plant_resource
from backend.rules.common.regions import regions_in_play
from backend.rules.common.turn_order import advance_turn
from backend.rules.phase_five_bureaucracy.bureaucracy import bureaucracy
from backend.rules.phase_four_building_houses.building_houses import buy_houses
from backend.rules.phase_one_turn_order.initial_order import determine_initial_order
from backend.rules.phase_three_resource_buying.resource_buying import buy_resources, quote_resources
from backend.rules.phase_two_auction.auction import (
    discard_power_plant,
    pass_bid,
    place_bid,
    select_power_plant,
)

# -------------------------------------------------------------------------------------------------
# Game service

class GameService:
    """The only way to read or change the game: one lock, turn checks, rules and saving."""

    def __init__(self, state, save_state, plant_slots_per_player=3, rng=None):
        self._state = state
        self._save_state = save_state
        self._plant_slots_per_player = plant_slots_per_player
        self._rng = rng
        self._lock = RLock()
        self._regions_in_play = regions_in_play(self._state, load_number_of_areas())
        self._city_regions = {
            name: region.casefold()
            for name, region, _, _ in load_map()["cities_positions"]
        }

    # ---------------------------------------------------------------------------------------------
    # Reading and saving

    def snapshot(self):
        """Return a copy of the state, so readers never see a half-finished action."""
        with self._lock:
            return deepcopy(self._state)

    def save_game(self):
        """Write the current state to the save game."""
        with self._lock:
            if not self._state.game_started:
                return ErrorCode.E_NOT_OKAY

            self._save_state(self._state)

            return ErrorCode.E_OK

    # ---------------------------------------------------------------------------------------------
    # Phase handling

    def _play_turn(self, player, required_action, rule):
        """Run a rule for the current player, end their turn and move on when everyone is done."""
        with self._lock:
            # Stale requests are rejected before the rule can change anything.
            if player != self._state.current_player:
                return ErrorCode.E_NOT_OKAY
            if player not in self._state.player_turn_order:
                return ErrorCode.E_NOT_OKAY
            if self._state.current_action != required_action:
                return ErrorCode.E_NOT_OKAY

            code = rule(self._state)

            if code != ErrorCode.E_OK:
                return code

            phase = phase_key(required_action)
            mark_phase_finished(self._state, phase, player)
            code = advance_turn(self._state, player)

            if code != ErrorCode.E_OK:
                return code

            if all_players_finished(self._state, phase):
                clear_phase_finished(self._state, phase)
                self._start_next_phase(phase)

            return ErrorCode.E_OK

    def _start_next_phase(self, finished_phase):
        """Start the phase that follows the finished one (phase two ends inside the auction rules)."""
        if finished_phase == PHASE_THREE_RESOURCE_BUYING:
            start_phase_four(self._state)

        elif finished_phase == PHASE_FOUR_BUILDING_HOUSES:
            start_phase_five(self._state)

        elif finished_phase == PHASE_FIVE_BUREAUCRACY:
            self._start_next_cycle()

    def _start_next_cycle(self):
        """Go back to phase one, which immediately sets the order and starts the auction."""
        self._state.cycles += 1
        self._state.phase = 1
        self._state.current_action = DETERMINING_PLAYER_ORDER

        determine_initial_order(self._state, self._rng)

    # ---------------------------------------------------------------------------------------------
    # Phase two: auction

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

    # ---------------------------------------------------------------------------------------------
    # Phase three: resources

    def quote_resources(self, player, resources):
        with self._lock:
            return quote_resources(self._state, player, resources)

    def buy_resources(self, player, resources):
        def rule(state):
            return buy_resources(state, player, resources)

        return self._play_turn(player, BUYING_RESOURCES, rule)

    # ---------------------------------------------------------------------------------------------
    # Phase four: houses

    def toggle_house_spot(self, city, spot):
        """Select a free house spot, or deselect it when it is already selected."""
        with self._lock:
            if self._state.current_action != BUILDING_HOUSES:
                return ErrorCode.E_NOT_OKAY
            if self._city_regions.get(city) not in self._regions_in_play:
                return ErrorCode.E_NOT_OKAY

            spots = self._state.map_houses.get(city)

            if spots is None or spot not in spots or spots[spot] is not None:
                return ErrorCode.E_NOT_OKAY

            selection = {"city": city, "spot": spot}

            if selection in self._state.pending_houses:
                self._state.pending_houses.remove(selection)
            else:
                self._state.pending_houses.append(selection)

            return ErrorCode.E_OK

    def buy_houses(self, player):
        def rule(state):
            return buy_houses(state, player, state.pending_houses)

        return self._play_turn(player, BUILDING_HOUSES, rule)

    # ---------------------------------------------------------------------------------------------
    # Phase five: bureaucracy

    def toggle_ready_to_power(self, player, plant_id):
        """Flip whether a plant of the player is ready to produce power."""
        with self._lock:
            plant = find_player_plant(self._state, player, plant_id)

            if plant is None:
                return ErrorCode.E_NOT_OKAY

            plant["ready_to_power"] = not plant["ready_to_power"]

            return ErrorCode.E_OK

    def bureaucracy(self, player):
        def rule(state):
            return bureaucracy(state, player)

        return self._play_turn(player, BUREAUCRACY, rule)

    # ---------------------------------------------------------------------------------------------
    # Any phase

    def transfer_resource(self, player, source_plant_id, source_slot, target_plant_id, target_slot):
        """Move one fuel unit between two plants of the player."""
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
