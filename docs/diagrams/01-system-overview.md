# System overview

How the browser, the Flask server, and the JSON files connect.

```mermaid
flowchart LR
    subgraph Browser["Browser (ui/)"]
        Start["start.html and start.js: player count, new/load"]
        UI["main.js and the render modules"]
        API["api.js: fetchView and POST actions"]
        Start --> API
        UI --> API
    end

    subgraph Server["Flask server (backend/server/)"]
        Routes["routes.py: new game, load game, view and actions"]
        Views["views/: build the view"]
        Service["application/game_service.py: coordinate commands and state"]
        Setup["game_setup/new_game.py: fresh randomized game state"]
        Rules["rules/phase_*/ and rules/common/"]
        State["rules/common/game_state.py: Python-defined in-memory state"]
        PhaseState["rules/common/phase_state.py: phase completion markers"]
        Data["data/files.py: static JSON files"]
        SaveData["data/game_state_store.py: load and save"]
        Routes --> Views
        Routes --> Service
        Routes --> Setup
        Views --> State
        Views --> PhaseState
        Service --> State
        Service --> PhaseState
        Service --> Rules
        Service --> Data
        Service --> SaveData
        SaveData --> Save
        Views --> Data
        Views --> Rules
    end

    subgraph Files["game_info/ (JSON files)"]
        Saves[("game_save/power_grid_game_save_<timestamp>.json<br/>timestamped snapshots")]
        Settings["static_info/power_grid_settings.json<br/>rules, texts, colors"]
        Resources["static_info/power_grid_resource_prices.json<br/>resources, price scales"]
        Deck["static_info/power_grid_deck_set_0.json<br/>power plants"]
        Money["static_info/power_grid_money.json"]
        Replen["static_info/power_grid_replenishment.json"]
        Map["maps/germany/power_grid_germany_map.json<br/>cities, connections"]
        Outline["maps/germany/germany_outline_dark.png"]
    end

    API -- "GET /api/view" --> Routes
    API -- "POST /api/new-game, /api/load-game" --> Routes
    API -- "GET /api/game-saves" --> Routes
    API -- "GET /api/view, POST /api/..." --> Routes
    Routes -- "static files (ui/, game_info/)" --> UI
    Data --> Settings
    Data --> Resources
    Data --> Deck
    Data --> Money
    Data --> Replen
    Data --> Map
    UI -. "image" .-> Outline
```

[Back to documentation](../index.md)
