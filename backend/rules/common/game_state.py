# -------------------------------------------------------------------------------------------------
# Imports

from __future__ import annotations

from dataclasses import asdict, dataclass, field

# -------------------------------------------------------------------------------------------------
# Game state

@dataclass
class GameState:
    number_of_players: int
    regions_chosen: list[str]
    rounds_played: int
    step: int
    phase: int
    power_plant_market: list[int]
    power_plant_deck: list[int]
    resource_market: dict[str, int]
    player_turn_order: list[str]
    current_player: str
    current_action: str
    player_aliases: dict[str, str]
    player_money: dict[str, int]
    player_power_plants: dict[str, list[dict]]
    map_houses: dict[str, dict[str, str | None]]
    pending_houses: list[dict[str, str]]
    cycles: int = 0
    player_colors: dict[str, str] = field(default_factory=dict)
    removed_power_plants: list[int] = field(default_factory=list)

    # These fields let an in-progress auction resume from a saved game.
    auction_starter: str | None = None
    selected_power_plant: int | None = None
    auction_participants: list[str] = field(default_factory=list)
    auction_bids: dict[str, int] = field(default_factory=dict)
    auction_passed: list[str] = field(default_factory=list)
    auction_skipped: list[str] = field(default_factory=list)
    players_bought_power_plant: list[str] = field(default_factory=list)
    phase_finished_players: dict[str, list[str]] = field(default_factory=dict)

    # Set while a winner chooses which existing plant to discard.
    pending_plant_replacement: dict | None = None

    def to_dict(self):
        return asdict(self)

# -------------------------------------------------------------------------------------------------
# Player colors

def default_player_colors(player_aliases, palette):
    """Give every player a color in roster order; the palette repeats if it is too short."""
    colors = {}

    for index, player in enumerate(player_aliases):
        colors[player] = palette[index % len(palette)]

    return colors