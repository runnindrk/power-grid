# -------------------------------------------------------------------------------------------------
# Imports

from backend.rules.common.error_codes import ErrorCode
from backend.rules.common.game_state import GameState
from backend.rules.common.phase_state import clear_phase_finished, mark_phase_finished
from backend.rules.phase_one_turn_order.initial_order import determine_order_after_first_auction

# -------------------------------------------------------------------------------------------------
# Auction helpers

def _next_player(state, player, candidates):
    if not candidates:
        return None

    current_index = state.player_turn_order.index(player)
    for offset in range(1, len(state.player_turn_order) + 1):
        candidate_index = (current_index + offset) % len(state.player_turn_order)
        candidate = state.player_turn_order[candidate_index]
        if candidate in candidates:
            return candidate

    return None


def _advance_to_resource_buying(state, player):
    state.selected_power_plant = None
    state.auction_participants.clear()
    state.auction_bids.clear()
    state.auction_passed.clear()
    state.auction_skipped.clear()
    state.players_bought_power_plant.clear()
    state.auction_starter = None
    state.pending_plant_replacement = None
    clear_phase_finished(state, "phase_two_auction")
    if state.cycles == 0:
        determine_order_after_first_auction(state)
    else:
        state.current_player = state.player_turn_order[0]
        state.current_action = "buying_resources"
        state.phase = 3


def _continue_after_award(state, winner, auction_starter):
    # A different winner does not consume the selector's turn.
    if auction_starter != winner and auction_starter not in state.players_bought_power_plant:
        state.current_player = auction_starter
        state.current_action = "power_plant_auction"
        return

    eligible = [
        player
        for player in state.player_turn_order
        if player not in state.players_bought_power_plant
    ]
    next_player = _next_player(state, winner, eligible)
    if next_player is None:
        _advance_to_resource_buying(state, winner)
    else:
        state.current_player = next_player
        state.current_action = "power_plant_auction"


def _new_power_plant(plant_id):
    return {
        "plant_id": plant_id,
        "resources": {
            "coal": 0,
            "oil": 0,
            "trash": 0,
            "gas": 0,
            "uranium": 0,
        },
        "ready_to_power": False,
    }


def _clear_auction(state):
    """Clear temporary bids and participants after resolving one plant auction."""
    state.selected_power_plant = None
    state.auction_participants.clear()
    state.auction_bids.clear()
    state.auction_passed.clear()
    state.auction_skipped.clear()
    state.auction_starter = None


def _award_power_plant(state, winner, plant_slots_per_player):
    plant_id = state.selected_power_plant
    auction_starter = state.auction_starter

    # Passed players' old bids are no longer active and cannot set the price.
    winning_bid = max(
        bid for player, bid in state.auction_bids.items()
        if player not in state.auction_passed
    )
    state.player_money[winner] -= winning_bid
    state.power_plant_market.remove(plant_id)
    if state.power_plant_deck:
        # Keep the market full by drawing its next plant from the persisted deck.
        state.power_plant_market.append(state.power_plant_deck.pop(0))
        state.power_plant_market.sort()
    state.players_bought_power_plant.append(winner)
    _clear_auction(state)

    # Pause the auction until the winner chooses a plant to discard.
    if len(state.player_power_plants[winner]) >= plant_slots_per_player:
        state.pending_plant_replacement = {
            "player": winner,
            "plant_id": plant_id,
            "auction_starter": auction_starter,
        }
        state.current_player = winner
        state.current_action = "discard_power_plant"
        return

    state.player_power_plants[winner].append(_new_power_plant(plant_id))
    mark_phase_finished(state, "phase_two_auction", winner)
    _continue_after_award(state, winner, auction_starter)


def select_power_plant(state: GameState, plant_id, plant_slots_per_player):
    """Select a plant and automatically make the opening bid at its minimum price."""
    player = state.current_player
    if (
        state.current_action != "power_plant_auction"
        or plant_id not in state.power_plant_market
    ):
        return ErrorCode.E_NOT_OKAY
    if player in state.players_bought_power_plant or player in state.auction_skipped:
        return ErrorCode.E_NOT_OKAY
    if state.player_money[player] < plant_id:
        return ErrorCode.E_NOT_OKAY

    participants = [
        candidate for candidate in state.player_turn_order
        if candidate not in state.players_bought_power_plant
        and candidate not in state.auction_skipped
    ]
    state.auction_starter = player
    state.selected_power_plant = plant_id
    state.auction_participants = participants
    state.auction_bids = {player: plant_id}
    state.auction_passed = []
    state.current_action = "power_plant_bidding"

    next_player = _next_player(state, player, participants)
    if len(participants) == 1:
        _award_power_plant(state, player, plant_slots_per_player)
    else:
        state.current_player = next_player

    return ErrorCode.E_OK


def highest_active_bid(state: GameState):
    return max(
        (bid for player, bid in state.auction_bids.items() if player not in state.auction_passed),
        default=0,
    )


def place_bid(state: GameState, player, amount, plant_slots_per_player):
    """Record a valid higher bid and pass the bidding turn to the next player."""
    if state.current_action != "power_plant_bidding" or player != state.current_player:
        return ErrorCode.E_NOT_OKAY
    if player not in state.auction_participants or player in state.auction_passed:
        return ErrorCode.E_NOT_OKAY
    if not isinstance(amount, int) or isinstance(amount, bool):
        return ErrorCode.E_NOT_OKAY

    highest_bid = highest_active_bid(state)
    if (
        player not in state.player_money
        or amount <= highest_bid
        or amount > state.player_money[player]
    ):
        return ErrorCode.E_NOT_OKAY

    state.auction_bids[player] = amount
    active_players = [
        candidate for candidate in state.auction_participants
        if candidate not in state.auction_passed
    ]
    if len(active_players) == 1:
        _award_power_plant(state, player, plant_slots_per_player)
    else:
        state.current_player = _next_player(state, player, active_players)

    return ErrorCode.E_OK


def pass_bid(state: GameState, player, plant_slots_per_player):
    """Skip selecting a plant or leave the current plant auction."""
    if player != state.current_player:
        return ErrorCode.E_NOT_OKAY

    if state.current_action == "power_plant_auction":
        if player in state.players_bought_power_plant or player in state.auction_skipped:
            return ErrorCode.E_NOT_OKAY

        # This pass applies only to the next auction selection, not later rounds.
        state.auction_skipped.append(player)
        eligible = [
            candidate for candidate in state.player_turn_order
            if candidate not in state.players_bought_power_plant
            and candidate not in state.auction_skipped
        ]
        next_player = _next_player(state, player, eligible)
        if next_player is None:
            _advance_to_resource_buying(state, player)
        else:
            state.current_player = next_player
        return ErrorCode.E_OK

    if state.current_action != "power_plant_bidding":
        return ErrorCode.E_NOT_OKAY
    if player not in state.auction_participants or player in state.auction_passed:
        return ErrorCode.E_NOT_OKAY

    state.auction_passed.append(player)
    active_players = [
        candidate for candidate in state.auction_participants
        if candidate not in state.auction_passed
    ]
    if len(active_players) == 1:
        _award_power_plant(state, active_players[0], plant_slots_per_player)
    elif not active_players:
        state.auction_passed.remove(player)
        return ErrorCode.E_NOT_OKAY
    else:
        state.current_player = _next_player(state, player, active_players)

    return ErrorCode.E_OK


def discard_power_plant(state: GameState, player, plant_id):
    """Discard an owned plant and install the plant waiting for replacement."""
    pending = state.pending_plant_replacement
    if (
        state.current_action != "discard_power_plant"
        or pending is None
        or player != state.current_player
        or player != pending["player"]
    ):
        return ErrorCode.E_NOT_OKAY

    plants = state.player_power_plants[player]
    discarded_index = next(
        (index for index, plant in enumerate(plants) if plant["plant_id"] == plant_id),
        None,
    )
    if discarded_index is None:
        return ErrorCode.E_NOT_OKAY

    plants.pop(discarded_index)
    plants.append(_new_power_plant(pending["plant_id"]))
    state.pending_plant_replacement = None
    mark_phase_finished(state, "phase_two_auction", player)
    _continue_after_award(state, player, pending["auction_starter"])

    return ErrorCode.E_OK