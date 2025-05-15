# Tech Context - UIKitX v2

This document outlines key technical details, stack information, constraints, and useful tips for working with the UIKitX v2 project.

## Core Stack
- **Language**: Python 3.10+
- **UI Framework**: Dash (Plotly)
- **Styling**: Dash Bootstrap Components, Custom CSS
- **Component Library**: Internal `uikitxv2` components (e.g., DataTable, Graph, Grid)

## TT REST API Integration (`TTRestAPI` package)

The `TTRestAPI` package manages authentication and communication with the Trading Technologies REST API.

### Environments & Configuration
- The API access is configured in `TTRestAPI/tt_config.py`.
- Supported environments are "UAT", "SIM", and "LIVE" (though LIVE credentials are not yet defined).
- The active environment is set by the `ENVIRONMENT` variable in `tt_config.py`.
- **UAT Environment**:
  - API String: `ext_uat_cert`
  - Credentials: `TT_API_KEY`, `TT_API_SECRET`
- **SIM Environment**:
  - API String: `ext_prod_sim`
  - Credentials: `TT_SIM_API_KEY`, `TT_SIM_API_SECRET`
- **LIVE Environment** (Future):
  - API String: `ext_prod_live`
  - Credentials: `TT_LIVE_API_KEY`, `TT_LIVE_API_SECRET` (to be added if needed)

### Token Management
- `TTRestAPI/token_manager.py` handles token acquisition and refresh.
- Tokens are stored in environment-specific JSON files in the `TTRestAPI` directory (e.g., `tt_token_uat.json`, `tt_token_sim.json`).
- The `TOKEN_FILE` variable in `tt_config.py` defines the base name for these files.

### Key Endpoints Used (Examples):
- `/ttpds/<env>/instrument/{instrumentId}`: Fetches details for a specific instrument.
- Other examples in `TTRestAPI/examples/` demonstrate usage for products, algos, etc.

## Logging (`lumberjack` module)
- Centralized logging setup in `src/lumberjack`.
- Decorators like `@TraceTime`, `@TraceMemory` use this system.
- Log data is stored in an SQLite database (`logs/uikittrace.db`).

## Development Tools & Practices
- **Static Analysis**: Ruff, MyPy (strict mode enforced via custom instructions).
- **Testing**: Pytest, with tests located in the `tests/` directory.
- **Memory Bank**: Key project information and evolving context is stored in the `memory-bank/` directory.
  - `code-index.md`: Summaries of code files.
  - `io-schema.md`: Definitions of inputs, outputs, constants.
  - `activeContext.md`: Current development focus.

## Architectural Principles
- Adherence to SOLID principles.
- ABC-first approach for new features (core interfaces in `src/core`).
- One component per file in `src/components`.
- No database access within decorators (except logger).
- Strict import paths (`from uikitxv2....`).

## UI Component Styling
- Default theme defined in `src/utils/colour_palette.py`.
- Components aim for a consistent, modern look and feel.
- The `ladderTest/laddertesting.py` example showcases a specific TT-style ladder with fixed styling.
