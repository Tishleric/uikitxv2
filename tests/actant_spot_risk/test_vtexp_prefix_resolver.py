from lib.trading.actant.spot_risk.vtexp_prefix_resolver import (
    extract_spot_prefix,
    resolve_time_symbol_from_prefix,
    resolve_time_symbol_from_key,
)


class FakeRosetta:
    def __init__(self, mapping: dict[str, str]):
        self.mapping = mapping

    def translate(self, symbol: str, src: str, dst: str) -> str:
        # Ignore src/dst in this fake; key off the symbol
        if symbol in self.mapping:
            return self.mapping[symbol]
        raise KeyError(symbol)


def test_extract_prefix_quarterly():
    assert extract_spot_prefix("XCME.OZN.SEP25.11.C") == "XCME.OZN.SEP25"


def test_extract_prefix_weekly():
    assert extract_spot_prefix("XCME.WY3.20AUG25.111.C") == "XCME.WY3.20AUG25"


def test_extract_prefix_malformed():
    assert extract_spot_prefix("") is None
    assert extract_spot_prefix("XCME.ZN") is None


def test_resolve_time_symbol_from_prefix():
    fake = FakeRosetta({
        "XCME.OZN.SEP25": "XCME.ZN.N.G.22AUG25",
    })
    assert resolve_time_symbol_from_prefix("XCME.OZN.SEP25", fake) == "XCME.ZN.N.G.22AUG25"


def test_resolve_time_symbol_from_prefix_missing():
    fake = FakeRosetta({})
    assert resolve_time_symbol_from_prefix("XCME.OZN.SEP25", fake) is None


def test_resolve_time_symbol_from_key_quarterly():
    fake = FakeRosetta({
        "XCME.OZN.SEP25": "XCME.ZN.N.G.22AUG25",
    })
    assert resolve_time_symbol_from_key("XCME.OZN.SEP25.11.C", fake) == "XCME.ZN.N.G.22AUG25"


def test_resolve_time_symbol_from_key_weekly():
    fake = FakeRosetta({
        "XCME.WY3.20AUG25": "XCME.ZN.N.G.20AUG25",
    })
    assert resolve_time_symbol_from_key("XCME.WY3.20AUG25.111.C", fake) == "XCME.ZN.N.G.20AUG25"

