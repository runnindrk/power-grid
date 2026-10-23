# -------------------------------------------------------------------------------------------------
# Actions (the value of GameState.current_action)

DETERMINING_PLAYER_ORDER = "determining_player_order"
POWER_PLANT_AUCTION = "power_plant_auction"
POWER_PLANT_BIDDING = "power_plant_bidding"
DISCARD_POWER_PLANT = "discard_power_plant"
BUYING_RESOURCES = "buying_resources"
BUILDING_HOUSES = "building_houses"
BUREAUCRACY = "bureaucracy"

# -------------------------------------------------------------------------------------------------
# Phases (the keys of GameState.phase_finished_players)

PHASE_ONE_TURN_ORDER = "phase_one_turn_order"
PHASE_TWO_AUCTION = "phase_two_auction"
PHASE_THREE_RESOURCE_BUYING = "phase_three_resource_buying"
PHASE_FOUR_BUILDING_HOUSES = "phase_four_building_houses"
PHASE_FIVE_BUREAUCRACY = "phase_five_bureaucracy"

# Several actions can belong to the same phase.
PHASE_BY_ACTION = {
    DETERMINING_PLAYER_ORDER: PHASE_ONE_TURN_ORDER,
    POWER_PLANT_AUCTION: PHASE_TWO_AUCTION,
    POWER_PLANT_BIDDING: PHASE_TWO_AUCTION,
    DISCARD_POWER_PLANT: PHASE_TWO_AUCTION,
    BUYING_RESOURCES: PHASE_THREE_RESOURCE_BUYING,
    BUILDING_HOUSES: PHASE_FOUR_BUILDING_HOUSES,
    BUREAUCRACY: PHASE_FIVE_BUREAUCRACY,
}

# -------------------------------------------------------------------------------------------------
# Resources

FUEL_RESOURCES = ["coal", "oil", "trash", "gas", "uranium"]
