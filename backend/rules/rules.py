import random
from enum import IntEnum
from typing import TypedDict


class ErrorCode(IntEnum):
    E_OK = 0
    E_NOT_OKAY = 1


class MapMatrix(TypedDict):
    matrix: list[list[int]]


class ResourceStock(TypedDict, total=False):
    coal: int
    oil: int
    trash: int
    uranium: int


class GameState(TypedDict):
    number_of_players: int
    regions_chosen: list[str]
    rounds_played: int
    step: int
    phase: int
    power_plant_market: list[int]
    resource_market: ResourceStock
    player_turn_order: list[str]
    current_player: str
    current_action: str
    player_aliases: dict[str, str]
    player_money: dict[str, int]
    player_power_plants: dict[str, list[int]]
    player_resources: dict[str, ResourceStock]
    map_houses: dict[str, dict]


# Phase 1: Determine player order
def determine_player_order(players: list[str]) -> list[str]:
    random.shuffle(players)
    return players

# Phase 2: Power Plant Auction
def auction_power_plant(plant_id: int, players: list[str], bids: dict[str, int]) -> str:
    highest_bidder = max(bids, key=bids.get)
    return highest_bidder

# Phase 3: Resource Buying
def buy_resources(player: str, resources: ResourceStock) -> tuple[int, ErrorCode]:
    return 0, ErrorCode.E_OK

# Phase 4: Building Houses
def build_houses(player: str, placements: list[dict[str, str]]) -> tuple[int, ErrorCode]:
    return 0, ErrorCode.E_OK

# Phase 5: Bureaucracy
def bureaucracy(state: GameState) -> None:
    for player in state["player_turn_order"]:
        pass  # Placeholder for bureaucracy logic