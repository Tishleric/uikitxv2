"""
Probe the UI classifier behavior for FUTURE vs unknown instrument_type for futures symbols.

This imports the classifier from the dashboard module without modifying it and runs a few scenarios.

Run:
  python diagnostics/ui_classifier_probe.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Import the function in-place by loading the module and fetching the nested function reference
import importlib


def load_classifier():
    mod = importlib.import_module('apps.dashboards.main.app')
    # _classify_instrument is defined inside update_positions_table; expose via attribute if available
    # Fallback: reconstruct a minimal version if not directly accessible.
    classify = getattr(mod, '_classify_instrument', None)
    if classify is None:
        # Build a minimal proxy using the same logic segments from the module
        fallback_futures = {
            'TYU5 Comdty', 'USU5 Comdty', 'FVU5 Comdty', 'TUU5 Comdty',
            'TYZ5 Comdty', 'USZ5 Comdty', 'FVZ5 Comdty', 'TUZ5 Comdty'
        }
        def proxy(row: dict) -> str:
            symbol = (row.get('symbol') or '').strip()
            if symbol in fallback_futures:
                return 'FUTURE'
            itype = str(row.get('instrument_type') or '').upper().strip()
            if itype in {'F', 'FUTURE'}:
                return 'FUTURE'
            if itype in {'C', 'P', 'CALL', 'PUT', 'OPTION'}:
                return 'OPTION'
            return 'OPTION'
        return proxy
    return classify


def main() -> None:
    classify = load_classifier()
    scenarios = [
        {'symbol': 'TYZ5 Comdty', 'instrument_type': ''},
        {'symbol': 'TYZ5 Comdty', 'instrument_type': None},
        {'symbol': 'TYZ5 Comdty', 'instrument_type': 'FUTURE'},
        {'symbol': 'USZ5 Comdty', 'instrument_type': ''},
        {'symbol': 'USZ5 Comdty', 'instrument_type': 'FUTURE'},
    ]
    print('symbol | instrument_type_in | classified_as')
    for sc in scenarios:
        result = classify(sc)
        print(f"{sc['symbol']} | {sc['instrument_type']} | {result}")


if __name__ == '__main__':
    main()




