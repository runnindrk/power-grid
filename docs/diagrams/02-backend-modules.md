# Backend modules

Which backend Python module uses which. Rules never import from `server/`, `views/` or `application/`.

```mermaid
flowchart TD
    main["server/main.py<br/>starts the real game"]
    app["server/app.py<br/>create_app(game_service)"]
    routes["server/routes.py<br/>one route for each action"]
    helpers["server/request_helpers.py<br/>read payload, build reply"]
    service["application/game_service.py<br/>lock, turn checks, phase changes"]
    gview["views/game_view.py<br/>build_view and header"]
    mview["views/map_view.py<br/>map geometry and colors"]
    mkt["views/market_view.py<br/>plant market, resource market, income"]
    pview["views/player_view.py<br/>player rows and controls"]
    plview["views/plant_view.py<br/>plant cards and fuel storage"]
    data["data/files.py<br/>static JSON paths and reading"]
    store["data/game_state_store.py<br/>save game loading and writing"]

    subgraph Common["rules/common/"]
        state["game_state.py<br/>state model"]
        constants["constants.py<br/>action and phase names"]
        phaseState["phase_state.py<br/>who finished a phase"]
        phaseFlow["phase_flow.py<br/>start phase two to five"]
        turn["turn_order.py<br/>next player, end turn"]
        plants["player_plants.py<br/>owned plants"]
        houses["player_houses.py<br/>house count"]
        xfer["resource_transfer.py<br/>storage, moving fuel"]
        errors["error_codes.py"]
    end

    subgraph Phases["rules/phase_*/"]
        initial["phase_one_turn_order/initial_order.py"]
        auction["phase_two_auction/auction.py"]
        resources["phase_three_resource_buying/resource_buying.py"]
        buildHouses["phase_four_building_houses/building_houses.py"]
        bureau["phase_five_bureaucracy/bureaucracy.py"]
    end

    main --> app
    main --> service
    main --> store
    app --> routes
    routes --> helpers
    routes --> gview
    routes --> service

    service --> Phases
    service --> phaseFlow
    service --> phaseState
    service --> turn
    service --> plants
    service --> xfer
    service --> data
    store --> state
    store --> data

    auction --> initial
    auction --> phaseFlow
    auction --> turn
    initial --> phaseFlow
    phaseFlow --> phaseState
    phaseState --> constants

    gview --> mview
    gview --> mkt
    gview --> pview
    gview --> data
    mkt --> plview
    mkt --> auction
    pview --> plview
    pview --> auction
    plview --> xfer
```

## Where a rule change goes

| You want to change | File |
| --- | --- |
| A rule of one phase | `rules/phase_*/` |
| Who starts a phase, which phase follows | `rules/common/phase_flow.py` and `GameService._start_next_phase` |
| What a button or label shows | `views/` and `game_info/static_info/power_grid_settings.json` |
| A new action name or phase name | `rules/common/constants.py` (and an `action_labels` entry in the settings) |
| A new URL | `server/routes.py` |

[Back to documentation](../index.md)
