import unittest

from backend.data.files import load_plant_deck, load_resources
from backend.data.game_state_store import load_game_state
from backend.rules.common.constants import BUILDING_HOUSES, BUYING_RESOURCES
from backend.rules.common.error_codes import ErrorCode
from backend.rules.common.phase_state import (
    all_players_finished,
    clear_phase_finished,
    mark_phase_finished,
    phase_key,
)
from backend.rules.common.player_plants import highest_plant_id, new_power_plant
from backend.rules.common.resource_transfer import storage_capacity, transfer_plant_resource
from backend.rules.common.turn_order import advance_turn, next_player


class TurnOrderTests(unittest.TestCase):
    def setUp(self):
        self.state = load_game_state()
        self.p1, self.p2, self.p3, self.p4 = self.state.player_turn_order

    # The next player wraps around to the start of the turn order.
    def test_next_player_wraps_around(self):
        self.assertEqual(next_player(self.state, self.p4, [self.p1, self.p2]), self.p1)
        self.assertEqual(next_player(self.state, self.p1, [self.p3]), self.p3)

    # Without any candidate there is no next player.
    def test_next_player_without_candidates_is_none(self):
        self.assertIsNone(next_player(self.state, self.p1, []))

    # Only the current player can end their turn.
    def test_advance_turn_checks_the_player(self):
        self.state.current_player = self.p1

        self.assertEqual(advance_turn(self.state, self.p2), ErrorCode.E_NOT_OKAY)
        self.assertEqual(self.state.current_player, self.p1)
        self.assertEqual(advance_turn(self.state, self.p1), ErrorCode.E_OK)
        self.assertEqual(self.state.current_player, self.p2)


class PhaseStateTests(unittest.TestCase):
    def setUp(self):
        self.state = load_game_state()
        self.state.phase_finished_players = {}

    # Actions of the same phase share one marker list.
    def test_phase_key_groups_actions(self):
        self.assertEqual(phase_key("power_plant_bidding"), phase_key("discard_power_plant"))
        self.assertEqual(phase_key(BUYING_RESOURCES), "phase_three_resource_buying")

    # A player is marked once, and the phase is done when all players are marked.
    def test_mark_and_check_phase(self):
        for player in self.state.player_turn_order:
            self.assertFalse(all_players_finished(self.state, BUILDING_HOUSES))
            mark_phase_finished(self.state, BUILDING_HOUSES, player)
            mark_phase_finished(self.state, BUILDING_HOUSES, player)

        self.assertTrue(all_players_finished(self.state, BUILDING_HOUSES))

        clear_phase_finished(self.state, BUILDING_HOUSES)

        self.assertFalse(all_players_finished(self.state, BUILDING_HOUSES))


class PlayerPlantTests(unittest.TestCase):
    # A new plant starts empty and not ready to power.
    def test_new_power_plant_is_empty(self):
        plant = new_power_plant(13)

        self.assertEqual(plant["plant_id"], 13)
        self.assertEqual(sum(plant["resources"].values()), 0)
        self.assertFalse(plant["ready_to_power"])

    # A player without plants has the highest plant 0.
    def test_highest_plant_id(self):
        state = load_game_state()
        p1, p2 = state.player_turn_order[:2]
        state.player_power_plants = {p1: [new_power_plant(5), new_power_plant(30)], p2: []}

        self.assertEqual(highest_plant_id(state, p1), 30)
        self.assertEqual(highest_plant_id(state, p2), 0)


class ResourceTransferTests(unittest.TestCase):
    def setUp(self):
        self.state = load_game_state()
        self.player = self.state.player_turn_order[0]
        self.plants = load_plant_deck()
        self.resources = load_resources()["resources"]

        # Plants 4 and 10 both burn coal and store 4 units; one coal is stored in plant 4.
        self.source = new_power_plant(4)
        self.target = new_power_plant(10)
        self.source["resources"]["coal"] = 1
        self.state.player_power_plants = {self.player: [self.source, self.target]}

    def move(self, source_slot, target_slot):
        return transfer_plant_resource(
            self.state, self.player, 4, source_slot, 10, target_slot, self.plants, self.resources,
        )

    # Storage is twice the fuel need; a hybrid plant uses its larger fuel need only once.
    def test_storage_capacity(self):
        self.assertEqual(storage_capacity(self.plants[4], self.resources), 4)
        self.assertEqual(storage_capacity(self.plants[5], self.resources), 4)
        self.assertEqual(storage_capacity(self.plants[6], self.resources), 2)

    # A valid move takes one fuel unit from the source and puts it in the target.
    def test_valid_move(self):
        self.assertEqual(self.move(0, 0), ErrorCode.E_OK)
        self.assertEqual(self.source["resources"]["coal"], 0)
        self.assertEqual(self.target["resources"]["coal"], 1)

    def test_occupied_compatible_slot_swaps_resources(self):
        source = new_power_plant(5)
        target = new_power_plant(12)
        source["resources"]["coal"] = 1
        target["resources"]["oil"] = 1
        self.state.player_power_plants[self.player] = [source, target]

        code = transfer_plant_resource(
            self.state, self.player, 5, 0, 12, 0, self.plants, self.resources,
        )

        self.assertEqual(code, ErrorCode.E_OK)
        self.assertEqual(source["resources"]["coal"], 0)
        self.assertEqual(source["resources"]["oil"], 1)
        self.assertEqual(target["resources"]["oil"], 0)
        self.assertEqual(target["resources"]["coal"], 1)

    def test_incompatible_occupied_slot_swap_is_atomic(self):
        source = new_power_plant(4)
        target = new_power_plant(7)
        source["resources"]["coal"] = 1
        target["resources"]["oil"] = 1
        self.state.player_power_plants[self.player] = [source, target]

        code = transfer_plant_resource(
            self.state, self.player, 4, 0, 7, 0, self.plants, self.resources,
        )

        self.assertEqual(code, ErrorCode.E_NOT_OKAY)
        self.assertEqual(source["resources"]["coal"], 1)
        self.assertEqual(target["resources"]["oil"], 1)

    # A fuel unit can only be dragged from a filled space and dropped on the first free space.
    def test_invalid_moves_change_nothing(self):
        self.assertEqual(self.move(1, 0), ErrorCode.E_NOT_OKAY)
        self.assertEqual(self.move(0, 4), ErrorCode.E_NOT_OKAY)
        self.assertEqual(self.move(-1, 0), ErrorCode.E_NOT_OKAY)
        self.assertEqual(self.source["resources"]["coal"], 1)
        self.assertEqual(self.target["resources"]["coal"], 0)

    # A plant the player does not own cannot take part in a move.
    def test_unowned_plant_is_rejected(self):
        code = transfer_plant_resource(
            self.state, self.player, 4, 0, 99, 0, self.plants, self.resources,
        )

        self.assertEqual(code, ErrorCode.E_NOT_OKAY)


if __name__ == "__main__":
    unittest.main()
