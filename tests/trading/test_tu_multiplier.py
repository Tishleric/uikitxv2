import pandas as pd

from lib.trading.pnl_fifo_lifo.config import get_pnl_multiplier
from lib.trading.pnl_fifo_lifo.pnl_engine import calculate_unrealized_pnl


def test_get_pnl_multiplier_root_based():
    # TU root (2-year) should map to 2000 regardless of month
    assert get_pnl_multiplier('TUU5 Comdty') == 2000
    assert get_pnl_multiplier('TUZ5 Comdty') == 2000

    # Non-TU roots default to 1000
    assert get_pnl_multiplier('TYU5 Comdty') == 1000
    assert get_pnl_multiplier('FVZ5 Comdty') == 1000
    assert get_pnl_multiplier('USZ5 Comdty') == 1000


def test_calculate_unrealized_pnl_uses_tu_multiplier():
    # Build minimal unrealized positions for TUZ5 and TYU5
    positions_tu = pd.DataFrame([
        {
            'sequenceId': 'SEQ-001',
            'symbol': 'TUZ5 Comdty',
            'quantity': 1.0,
            'price': 100.0,  # entry
            'time': '2025-08-01 12:00:00.000',
            'buySell': 'B',
        }
    ])
    positions_ty = pd.DataFrame([
        {
            'sequenceId': 'SEQ-002',
            'symbol': 'TYU5 Comdty',
            'quantity': 1.0,
            'price': 100.0,  # entry
            'time': '2025-08-01 12:00:00.000',
            'buySell': 'B',
        }
    ])

    # Price dictionaries: use 'now' with current price 101.0
    price_dicts_tu = {
        'now': {'TUZ5 Comdty': 101.0},
        'close': {},
        'sodTod': {},
        'sodTom': {},
    }
    price_dicts_ty = {
        'now': {'TYU5 Comdty': 101.0},
        'close': {},
        'sodTod': {},
        'sodTom': {},
    }

    # Compute live unrealized PnL
    res_tu = calculate_unrealized_pnl(positions_tu, price_dicts_tu, method='live')
    res_ty = calculate_unrealized_pnl(positions_ty, price_dicts_ty, method='live')

    # TU uses 2000, TY uses 1000 for 1-point change * qty=1
    assert len(res_tu) == 1
    assert len(res_ty) == 1
    assert abs(res_tu[0]['unrealizedPnL'] - 2000.0) < 1e-9
    assert abs(res_ty[0]['unrealizedPnL'] - 1000.0) < 1e-9


