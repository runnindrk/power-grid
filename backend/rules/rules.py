# -------------------------------------------------------------------------------------------------
# Imports

from enum import IntEnum

# -------------------------------------------------------------------------------------------------
# Result codes

class ErrorCode(IntEnum):
    E_OK = 0
    E_NOT_OKAY = 1

# -------------------------------------------------------------------------------------------------
# Phase 2: Power plant auction (placeholders)

def place_bid(player, amount):
    """Placeholder: will record a bid from a player in the auction."""
    return ErrorCode.E_OK


def pass_bid(player):
    """Placeholder: will record that a player is out of the auction."""
    return ErrorCode.E_OK

# -------------------------------------------------------------------------------------------------
# Phase 3: Resource buying (placeholders)

def quote_resources(player, resources):
    """Placeholder: will return the price of the resources; always 0 for now."""
    return 0


def buy_resources(player, resources):
    """Placeholder: will buy the resources for a player."""
    return ErrorCode.E_OK

# -------------------------------------------------------------------------------------------------
# Phase 4: Building houses (placeholders)

def quote_houses(player, placements):
    """Placeholder: will return the price of the houses; always 0 for now."""
    return 0


def buy_houses(player, placements):
    """Placeholder: will buy houses in the selected city spots for a player."""
    return ErrorCode.E_OK

# -------------------------------------------------------------------------------------------------
# Phase 5: Bureaucracy (placeholders)

def bureaucracy(state):
    """Placeholder: will run the bureaucracy phase (powering plants and income)."""
    return ErrorCode.E_OK
