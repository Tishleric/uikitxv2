import pytest

from lib.trading.market_prices.rosetta_stone import RosettaStone


class TestRosettaStoneSeptemberFuturesReverse:
    @pytest.fixture
    def translator(self):
        return RosettaStone()

    @pytest.mark.parametrize(
        "actantrisk, actanttrades, bloomberg",
        [
            ("XCME.ZN.SEP25", "XCMEFFDPSX20250919U0ZN", "TYU5 Comdty"),
            ("XCME.ZT.SEP25", "XCMEFFDPSX20250930U0ZT", "TUU5 Comdty"),
            ("XCME.ZF.SEP25", "XCMEFFDPSX20250930U0ZF", "FVU5 Comdty"),
            ("XCME.ZB.SEP25", "XCMEFFDPSX20250919U0ZB", "USU5 Comdty"),
        ],
    )
    def test_september_futures_reverse_mappings(self, translator, actantrisk, actanttrades, bloomberg):
        # Forward sanity checks
        assert translator.translate(actantrisk, "actantrisk", "bloomberg") == bloomberg
        assert translator.translate(actanttrades, "actanttrades", "bloomberg") == bloomberg

        # Reverse lookups
        assert translator.translate(bloomberg, "bloomberg", "actantrisk") == actantrisk
        assert translator.translate(bloomberg, "bloomberg", "actanttrades") == actanttrades


