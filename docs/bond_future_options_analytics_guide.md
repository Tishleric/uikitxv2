## Bond Future Options Analytics – Orientation Guide

**Location**: `lib/trading/bond_future_options/`

### What lives here (math-first summary)
- `README.md`: Big-picture overview, quick start, and API examples.
- `__init__.py`: Exposes the public surface (API functions, facade, factory, model).
- `api.py`: Safe, direct functions for implied vol and Greeks. Handles defaults, scaling, and guards.
- `greek_calculator_api.py`: Facade. Accepts simple dicts/lists and delegates to a chosen model via the factory.
- `model_factory.py`: Central registry that creates model instances by name (e.g., `bachelier_v1`). Easy switch-over point.
- `option_model_interface.py`: Contract each model implements (`calculate_implied_vol`, `calculate_greeks`, etc.).
- `models/bachelier_v1.py`: Current model. Wraps core engine but conforms to the interface (consistent method names).
- `pricing_engine.py`: Core bond-future-specific engine that ties Bachelier math to DV01/convexity/yield context.
- `bachelier_greek.py`: Analytical Greek formulas (delta, gamma, vega, theta, volga, vanna, charm, speed, color, ultima, zomma). Defines scaling rules.
- `bachelier.py`: Pure Bachelier price/auxiliary math (distribution terms, helpers) used by the engine.
- `analysis.py`: Solvers and the canonical “calculate_all_greeks” sequence (ensures consistent scaling/order).
- `numerical_greeks.py`: Finite-difference Greeks for spot checks/validation (not used in production).
- `greek_validator.py`: Tools to compare analytical Greeks vs price changes (Taylor-based attribution).
- `example_usage.py`: Small runnable examples.

### How the model is chosen (ModelFactory)
- `ModelFactory` maps a model name → class (e.g., `'bachelier_v1'` → `BachelierV1`).
- `GreekCalculatorAPI` asks the factory for the model, then calls `calculate_implied_vol` and `calculate_greeks`.
- To switch models globally in callers that use the facade, register the new model and change the model name passed in.

### Where to start to review Greek accuracy (math-first path)
1) Read `docs/greek_formulae_documentation.md` for the exact closed-form definitions.
2) Open `bachelier_greek.py` and verify each formula/scale matches the docs (note: most Y-space Greeks are scaled ×1000 for readability).
3) Inspect `analysis.py` → `calculate_all_greeks(...)` to see the canonical calculation/order and which terms are scaled.
4) Review `api.py` for default parameters, safeguards (min price, vol bounds), and optional unscaled output.
5) Cross-check with finite differences in `numerical_greeks.py` on a few points if desired.
6) Optional: run tests `tests/bond_future_options/test_api_alignment.py` and `tests/bond_future_options/test_factory_facade.py` to sanity-check results and the facade/factory flow.

### How production code uses this
- Live pipeline (spot-risk watcher) calls `GreekCalculatorAPI.analyze(...)` via `lib/trading/actant/spot_risk/calculator.py`.
- Option Greeks come from this library; futures rows use simple hardcoded Greeks (delta_F=1, etc.) outside the library.

### Key notions (for quants)
- Price space vs Yield space: the engine converts appropriately using DV01/convexity; many Y-space outputs are reported ×1000.
- Consistency: `analysis.calculate_all_greeks` is the single authority for which Greeks are computed and how they’re scaled.
- Swappability: Switching to a new model implementation doesn’t require changing call sites—use the factory/facade.

