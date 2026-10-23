# -------------------------------------------------------------------------------------------------
# Imports

from backend.rules.common.constants import (
    DISCARD_POWER_PLANT,
    POWER_PLANT_AUCTION,
    POWER_PLANT_BIDDING,
    PHASE_TWO_AUCTION,
)
from backend.rules.common.error_codes import ErrorCode
from backend.rules.common.game_state import GameState
from backend.rules.common.phase_flow import start_phase_three
from backend.rules.common.phase_state import mark_phase_finished
from backend.rules.common.player_plants import new_power_plant
from backend.rules.common.turn_order import next_player
from backend.rules.phase_one_turn_order.initial_order import order_by_highest_plant

# -------------------------------------------------------------------------------------------------
# Who is still in

def players_who_can_select(state: GameState):
    """Return the players, in turn order, who may still pick a plant in this auction round."""
    players = []

    for player in state.player_turn_order:
        if player in state.players_bought_power_plant:
            continue
        if player in state.auction_skipped:
            continue

        players.append(player)

    return players


def active_bidders(state: GameState):
    """Return the players, in turn order, who are still bidding on the selected plant."""
    players = []

    for player in state.auction_participants:
        if player not in state.auction_passed:
            players.append(player)

    return players


def highest_active_bid(state: GameState):
    """Return the highest bid of a player who has not passed; 0 if there is none."""
    highest = 0

    for player in active_bidders(state):
        highest = max(highest, state.auction_bids.get(player, 0))

    return highest

# -------------------------------------------------------------------------------------------------
# Ending the auction

def clear_current_auction(state: GameState):
    """Forget the bids and participants of the plant that was just resolved."""
    state.selected_power_plant = None
    state.auction_participants.clear()
    state.auction_bids.clear()
    state.auction_passed.clear()
    state.auction_skipped.clear()
    state.auction_starter = None


def finish_auction(state: GameState):
    """End the whole auction phase and start resource buying."""
    clear_current_auction(state)
    state.players_bought_power_plant.clear()
    state.pending_plant_replacement = None

    # In the first cycle the order for resource buying is set by the plants just bought.
    if state.cycles == 0:
        order_by_highest_plant(state)

    start_phase_three(state)


def continue_after_award(state: GameState, winner, auction_starter):
    """Give the turn to whoever selects the next plant, or end the auction if nobody is left."""
    # A different winner does not use up the turn of the player who selected the plant.
    if auction_starter != winner and auction_starter not in state.players_bought_power_plant:
        state.current_player = auction_starter
        state.current_action = POWER_PLANT_AUCTION
        return

    remaining = []

    for player in state.player_turn_order:
        if player not in state.players_bought_power_plant:
            remaining.append(player)

    following = next_player(state, winner, remaining)

    if following is None:
        finish_auction(state)
        return

    state.current_player = following
    state.current_action = POWER_PLANT_AUCTION


def award_power_plant(state: GameState, winner, plant_slots_per_player):
    """Let the winner pay the highest bid and take the selected plant."""
    plant_id = state.selected_power_plant
    auction_starter = state.auction_starter

    # Read the price before the auction state is cleared.
    state.player_money[winner] -= highest_active_bid(state)

    # The market is refilled from the top of the draw pile and kept sorted.
    state.power_plant_market.remove(plant_id)

    if state.power_plant_deck:
        state.power_plant_market.append(state.power_plant_deck.pop(0))
        state.power_plant_market.sort()

    state.players_bought_power_plant.append(winner)
    clear_current_auction(state)

    # With full slots the auction waits until the winner discards a plant.
    if len(state.player_power_plants[winner]) >= plant_slots_per_player:
        state.pending_plant_replacement = {
            "player": winner,
            "plant_id": plant_id,
            "auction_starter": auction_starter,
        }
        state.current_player = winner
        state.current_action = DISCARD_POWER_PLANT
        return

    state.player_power_plants[winner].append(new_power_plant(plant_id))
    mark_phase_finished(state, PHASE_TWO_AUCTION, winner)
    continue_after_award(state, winner, auction_starter)

# -------------------------------------------------------------------------------------------------
# Selecting a plant

def can_select_plant(state: GameState, plant_id):
    """Return True if the current player may select this market plant: they must afford its price."""
    player = state.current_player

    if state.current_action != POWER_PLANT_AUCTION:
        return False
    if plant_id not in state.power_plant_market:
        return False
    if player not in players_who_can_select(state):
        return False

    return state.player_money[player] >= plant_id


def select_power_plant(state: GameState, plant_id, plant_slots_per_player):
    """Select a plant from the market; the selector opens the bidding at the plant's price."""
    if not can_select_plant(state, plant_id):
        return ErrorCode.E_NOT_OKAY

    player = state.current_player
    selectors = players_who_can_select(state)

    state.auction_starter = player
    state.selected_power_plant = plant_id
    state.auction_participants = selectors
    state.auction_bids = {player: plant_id}
    state.auction_passed = []
    state.current_action = POWER_PLANT_BIDDING

    # Alone in the auction: the selector gets the plant without bidding.
    if len(selectors) == 1:
        award_power_plant(state, player, plant_slots_per_player)
    else:
        state.current_player = next_player(state, player, selectors)

    return ErrorCode.E_OK

# -------------------------------------------------------------------------------------------------
# Bidding

def place_bid(state: GameState, player, amount, plant_slots_per_player):
    """Record a bid that is higher than all active bids and that the player can pay."""
    if state.current_action != POWER_PLANT_BIDDING or player != state.current_player:
        return ErrorCode.E_NOT_OKAY
    if player not in state.auction_participants or player in state.auction_passed:
        return ErrorCode.E_NOT_OKAY

    # A boolean is an int in Python, but it is not a valid amount.
    if not isinstance(amount, int) or isinstance(amount, bool):
        return ErrorCode.E_NOT_OKAY
    if amount <= highest_active_bid(state) or amount > state.player_money[player]:
        return ErrorCode.E_NOT_OKAY

    state.auction_bids[player] = amount
    bidders = active_bidders(state)

    if len(bidders) == 1:
        award_power_plant(state, player, plant_slots_per_player)
    else:
        state.current_player = next_player(state, player, bidders)

    return ErrorCode.E_OK


def pass_bid(state: GameState, player, plant_slots_per_player):
    """Pass: skip choosing a plant, or leave the bidding of the selected plant."""
    if player != state.current_player:
        return ErrorCode.E_NOT_OKAY

    if state.current_action == POWER_PLANT_AUCTION:
        return _skip_selection(state, player)

    if state.current_action == POWER_PLANT_BIDDING:
        return _leave_bidding(state, player, plant_slots_per_player)

    return ErrorCode.E_NOT_OKAY


def _skip_selection(state: GameState, player):
    """Skip choosing a plant; the skip lasts only until the next plant is selected."""
    selectors = players_who_can_select(state)

    if player not in selectors:
        return ErrorCode.E_NOT_OKAY

    state.auction_skipped.append(player)
    following = next_player(state, player, players_who_can_select(state))

    if following is None:
        finish_auction(state)
    else:
        state.current_player = following

    return ErrorCode.E_OK


def _leave_bidding(state: GameState, player, plant_slots_per_player):
    """Leave the bidding; the last bidder left wins the plant."""
    if state.cycles == 0 and player == state.auction_starter:
        return ErrorCode.E_NOT_OKAY
    if player not in state.auction_participants or player in state.auction_passed:
        return ErrorCode.E_NOT_OKAY

    state.auction_passed.append(player)
    bidders = active_bidders(state)

    # Nobody could be left to take the plant, so the pass is undone.
    if not bidders:
        state.auction_passed.remove(player)
        return ErrorCode.E_NOT_OKAY

    if len(bidders) == 1:
        award_power_plant(state, bidders[0], plant_slots_per_player)
    else:
        state.current_player = next_player(state, player, bidders)

    return ErrorCode.E_OK

# -------------------------------------------------------------------------------------------------
# Discarding a plant

def discard_power_plant(state: GameState, player, plant_id):
    """Discard an owned plant and install the plant that was waiting for a free slot."""
    pending = state.pending_plant_replacement

    if state.current_action != DISCARD_POWER_PLANT or pending is None:
        return ErrorCode.E_NOT_OKAY
    if player != state.current_player or player != pending["player"]:
        return ErrorCode.E_NOT_OKAY

    plants = state.player_power_plants[player]
    discarded = None

    for plant in plants:
        if plant["plant_id"] == plant_id:
            discarded = plant

    if discarded is None:
        return ErrorCode.E_NOT_OKAY

    plants.remove(discarded)
    plants.append(new_power_plant(pending["plant_id"]))
    state.pending_plant_replacement = None

    mark_phase_finished(state, PHASE_TWO_AUCTION, player)
    continue_after_award(state, player, pending["auction_starter"])

    return ErrorCode.E_OK
