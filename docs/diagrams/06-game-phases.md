# Game phases

How `current_action` moves through one cycle. Phase two is ended by the auction rules; the other phases are ended by `GameService` when every player has finished.

```mermaid
stateDiagram-v2
    [*] --> determining_player_order: new cycle
    determining_player_order --> power_plant_auction: initial_order.py sets the order

    state "Phase two" as P2 {
        power_plant_auction --> power_plant_bidding: select plant
        power_plant_bidding --> power_plant_auction: winner has a free slot
        power_plant_bidding --> discard_power_plant: winner has full slots
        discard_power_plant --> power_plant_auction: plant discarded
    }

    power_plant_auction --> buying_resources: all selected or passed
    buying_resources --> building_houses: all players finished
    building_houses --> bureaucracy: all players finished
    bureaucracy --> determining_player_order: all players finished, cycles + 1
```

[Back to documentation](../index.md)
