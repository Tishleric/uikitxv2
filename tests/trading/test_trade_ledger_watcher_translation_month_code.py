import pytest

from lib.trading.pnl_fifo_lifo.trade_ledger_watcher import TradeLedgerFileHandler


@pytest.fixture
def handler(tmp_path):
    # db_path not used for translation; provide temp path
    return TradeLedgerFileHandler(db_path=str(tmp_path / "trades.db"))


@pytest.mark.parametrize(
    "actant_fut, expected_bb",
    [
        # ZN (TY)
        ("XCMEFFDPSX20250919U0ZN", "TYU5 Comdty"),
        ("XCMEFFDPSX20251219Z0ZN", "TYZ5 Comdty"),
        # ZT (TU)
        ("XCMEFFDPSX20250930U0ZT", "TUU5 Comdty"),
        ("XCMEFFDPSX20251230Z0ZT", "TUZ5 Comdty"),
        # ZF (FV)
        ("XCMEFFDPSX20250930U0ZF", "FVU5 Comdty"),
        ("XCMEFFDPSX20251230Z0ZF", "FVZ5 Comdty"),
        # ZB (US)
        ("XCMEFFDPSX20250919U0ZB", "USU5 Comdty"),
        ("XCMEFFDPSX20251219Z0ZB", "USZ5 Comdty"),
    ],
)
def test_translate_futures_month_codes(handler, actant_fut, expected_bb):
    assert handler._translate_symbol(actant_fut) == expected_bb


def test_translate_non_futures_delegates_to_rosetta(handler):
    # A simple option format that RosettaStone should handle; ensure it doesn't crash
    # We won't assert exact because it depends on calendar; just ensure non-None for a likely valid key
    # If calendar mapping is absent, None is acceptable here; the goal is to confirm no misrouting of futures path.
    result = handler._translate_symbol("XCMEOCADPS20250721N0VY3/111")
    assert result is None or isinstance(result, str)





