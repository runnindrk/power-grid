# System overview

How the browser, the Flask server, and the JSON files connect.

```mermaid
flowchart LR
    subgraph Browser["Browser (ui/)"]
        UI["main.js and the render modules"]
        API["api.js: fetchView and POST actions"]
        UI --> API
    end

    subgraph Server["Flask server (backend/server/main.py)"]
        Routes["Routes: GET /api/view, POST actions"]
        Views["views/: build the view"]
        Service["application/game_service.py: coordinate commands and state"]
        Rules["rules/phase_*/ and rules/common/"]
        State["rules/common/game_state.py: Python-defined in-memory state"]
        PhaseState["rules/common/phase_state.py: phase completion markers"]
        Data["data/files.py: static JSON files"]
        SaveData["data/game_state_store.py: load and save"]
        Routes --> Views
        Routes --> Service
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
        Save[("game_state/power_grid_game_state.json<br/>saved game snapshot")]
        Settings["static_info/power_grid_settings.json<br/>rules, texts, colors"]
        Resources["static_info/power_grid_resource_prices.json<br/>resources, price scales"]
        Deck["static_info/power_grid_deck_set_0.json<br/>power plants"]
        Money["static_info/power_grid_money.json"]
        Replen["static_info/power_grid_replenishment.json"]
        Map["maps/germany/power_grid_germany_map.json<br/>cities, connections"]
        Outline["maps/germany/germany_outline_dark.png"]
    end

    API -- "GET /api/view" --> Routes
    API -- "POST /api/..." --> Routes
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
